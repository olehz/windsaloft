from math import atan2, degrees, floor
from collections import deque, defaultdict
from random import shuffle
from geojson import FeatureCollection, Feature, MultiLineString
from .utils import smooth_line


class JetStream:
    def __init__(self, u_data, v_data, **kwargs) -> None:
        if (
                len(u_data) <= 1
                or len(v_data) <= 1
                or len(u_data[0]) <= 1
                or len(v_data[0]) <= 1
        ):
            raise TypeError("Raster is too small")

        if len(u_data) != len(v_data) or len(u_data[0]) != len(v_data[0]):
            raise TypeError("Raster components are not the same shape")

        self.u_data = u_data
        self.v_data = v_data
        self.x_size = len(self.u_data[0])
        self.y_size = len(self.u_data)
        self.pixel_size = 180 / (self.y_size - 1)

        self.pixel_dist = kwargs.get("pixel_dist", 5)
        self.smooth = kwargs.get("smooth", 0)
        self.zigzag_degrees = kwargs.get("zigzag_degrees", 30)
        self.min_length = kwargs.get("min_length", 30)
        self.min_value = kwargs.get("min_value", 0) ** 2

        self.used_pixels = [[False] * self.x_size for _ in range(self.y_size)]

    def _is_outside(self, x, y) -> bool:
        return x < 0 or x >= self.x_size or y < 0 or y >= self.y_size

    def _is_pixel_free(self, x0, y0) -> bool:
        if self._is_outside(x0, y0):
            return False

        x_lo = max(x0 - self.pixel_dist, 0)
        x_hi = min(x0 + self.pixel_dist, self.x_size - 1)
        y_lo = max(y0 - self.pixel_dist, 0)
        y_hi = min(y0 + self.pixel_dist, self.y_size - 1)
        for x in range(x_lo, x_hi + 1):
            for y in range(y_lo, y_hi + 1):
                if self.used_pixels[y][x]:
                    return False
        return True

    def _get_shift(self, x: float) -> int:
        if x < 0 or x >= self.x_size:
            return int(x // self.x_size) * -self.x_size
        return 0

    def _get_line(self, x0: int, y0: int):
        # Verify that seed point is available
        if self._is_outside(x0, y0) or self.used_pixels[y0][x0]:
            return []

        line_found = False
        line = deque([[x0, y0]])
        # Trace forward/backward from seed point
        for step in [1, -1]:
            x = x0
            y = y0
            prev_dir = float("-inf")
            while True:
                val = self._get_value_at_point(x + self._get_shift(x), y)
                # Zero speed points are problematic
                if val["u"] + val["v"] == 0:
                    self.used_pixels[y0][x0] = True
                    break

                x += val["u"] * step
                y += -val["v"] * step

                xr, yr = round(x), round(y)
                xr += self._get_shift(xr)
                if yr < 0 or yr >= self.y_size or self.used_pixels[yr][xr]:
                    break

                # Skip ZigZag
                curr_dir = round(degrees(atan2(val["u"], val["v"])))
                if prev_dir > float("-inf"):
                    diff_dir = abs(prev_dir - curr_dir)
                    diff_dir = min(diff_dir, abs(360 - diff_dir))
                    if diff_dir > self.zigzag_degrees:
                        break
                prev_dir = curr_dir

                if step == 1:
                    line.append([x, y])
                else:
                    line.appendleft([x, y])

                line_found = True
                self.used_pixels[yr][xr] = True
        if line_found and len(line) > self.min_length:
            self.used_pixels[y0][x0] = True
            return list(line)
        return []

    def _get_value_at_point(self, x: float, y: float) -> dict:
        # x/y indices below and above the cell to interpolate in .
        # If minmax affects an index then we're on or outside the border
        # and we will do implicit linear extrapolation out to any distance.
        x0 = floor(x)
        x1 = (x0 + 1) % self.x_size

        y0 = min(max(floor(y), 0), self.y_size - 2)
        y1 = y0 + 1

        # Linear weights along x/y axes
        xw1 = x - x0
        xw0 = 1 - xw1
        yw1 = y - y0
        yw0 = 1 - yw1

        # Bi-linear weights of the 4 corner points
        pw00 = yw0 * xw0
        pw01 = yw1 * xw0
        pw10 = yw0 * xw1
        pw11 = yw1 * xw1

        # Interpolate the U, V vector components
        u = (
                self.u_data[y0][x0] * pw00
                + self.u_data[y0][x1] * pw01
                + self.u_data[y1][x0] * pw10
                + self.u_data[y1][x1] * pw11
        )

        v = (
                self.v_data[y0][x0] * pw00
                + self.v_data[y0][x1] * pw01
                + self.v_data[y1][x0] * pw10
                + self.v_data[y1][x1] * pw11
        )

        # Scale u, v vector to make one of the components at least one so the trace steps into a new cell.
        # Don't divide by 0 but instead pass 0-vectors through unchanged to be handled by the caller
        mdl = max(abs(u), abs(v)) or 1
        return {"u": u / mdl, "v": v / mdl}

    def _xy2lonlat(self, x: float, y: float):
        return (
            x * self.pixel_size - 180,
            y * -self.pixel_size + 90
        )

    def _split_by_date_line(self, line):
        # Split an input linestring in EPSG:4326 against the -180/180 date line
        px, py = line[0]
        shift = self._get_shift(px)
        prev = shift
        geo_lines = [[self._xy2lonlat(px + shift, py)]]
        group = 0
        for i in range(1, len(line)):
            x, y = line[i]
            shift = self._get_shift(x)
            if shift != prev:
                group += 1
                geo_lines.append([])

                if x > px:
                    ny = py + (y - py) * (self.x_size - px % self.x_size) / (x - px)
                    geo_lines[group-1].append(self._xy2lonlat(self.x_size, ny))
                    geo_lines[group].append(self._xy2lonlat(0, ny))
                else:
                    ny = py + (y - py) * (px % self.x_size) / (px - x)
                    geo_lines[group-1].append(self._xy2lonlat(0, ny))
                    geo_lines[group].append(self._xy2lonlat(self.x_size, ny))
                prev = shift
            px, py = x, y
            geo_lines[group].append(self._xy2lonlat(x + shift, y))
        return MultiLineString(geo_lines)

    def _gen_starting_points(self):
        speed_groups = defaultdict(list)
        for y in range(self.y_size):
            for x in range(self.x_size):
                v = self.u_data[y][x] ** 2 + self.v_data[y][x] ** 2
                if v < self.min_value:
                    self.u_data[y][x] = 0
                    self.v_data[y][x] = 0
                    continue

                speed_groups[round(v)].append([x, y])
        for _, coords in sorted(speed_groups.items(), reverse=True):
            yield from coords

    def to_geojson(self):
        # Iterate over all grid points in pseudo-random order and try to start a line there
        idx = 0
        features = []
        for x, y in self._gen_starting_points():
            if self._is_pixel_free(x, y):
                line = self._get_line(x, y)
                if line:
                    properties = {"id": idx}
                    line = smooth_line(line, self.smooth)
                    f = Feature(geometry=self._split_by_date_line(line), properties=properties)
                    features.append(f)
                    idx += 1

        return FeatureCollection(features)


def jet_streams(u, v, **kwargs):
    s = JetStream(u, v, **kwargs)
    return s.to_geojson()
