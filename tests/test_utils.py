import numpy as np
from windsaloft.utils import smooth_line

def test_open_line_smooth():
    expected_pts = [[1, 0], [1.25, 2.5], [1.75, 7.5], [2, 10]]
    actual_pts = smooth_line([[1,0],[2,10]], 1)
    assert np.array_equal(actual_pts, expected_pts)
