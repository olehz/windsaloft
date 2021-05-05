def smooth_line(line, n: int = 2):
    # Smoothing lines using Chaikins algorithm
    first = line[0]
    last = line[-1]
    for _ in range(n):
        new_pts = [first]
        for i in range(1, len(line)):
            p0, p1 = line[i - 1], line[i]
            p0x, p0y = p0
            p1x, p1y = p1

            q = [0.75 * p0x + 0.25 * p1x, 0.75 * p0y + 0.25 * p1y]
            r = [0.25 * p0x + 0.75 * p1x, 0.25 * p0y + 0.75 * p1y]
            new_pts.extend([q, r])
        new_pts.append(last)
        line = new_pts
    return line