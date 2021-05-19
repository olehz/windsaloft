import numpy as np
from windsaloft.jetstream import jet_streams

def test_raster_base_coordinates_ne():
    w = 30
    Y, X = np.mgrid[-w:w:91j, -w:w:180j]
    u = -1 - X**2 + Y
    v = 1 + X - Y**2

    feature_collection = jet_streams(
        u, v, pixel_dist=30, min_value=10, smooth=0, zigzag_degrees=45)
    x, y = feature_collection.features[0].geometry.coordinates[0][0]
    assert x == -178.0
    assert y == 87.830286
