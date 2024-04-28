'''
geometrical calculations module
'''

from pygame import Vector2
from math import atan2, sqrt

def find_collision_centers_on_line(point: Vector2, point_on_line: Vector2, line_direction: Vector2, radius: float):
    # find distance between line and point. direction must be normalized
    ## calculate line equation m, b
    if line_direction[0] == 0:
        return None
    line_m = line_direction[1] / line_direction[0]  
    line_b = - line_m * point_on_line[0] + point_on_line[1]

    ## calculate line of point
    if line_m == 0:
        return None
    p_line_m = - 1.0 / line_m
    p_line_b = - p_line_m * point[0] + point[1]

    ## find intersection
    x_middle = (p_line_b - line_b) / (line_m - p_line_m)
    y_middle = line_m * x_middle + line_b
    middle = Vector2(x_middle, y_middle)

    ## calculate distance
    distance = middle.distance_to(point)

    # find the points
    arg = 4 * radius * radius - distance * distance
    if arg < 0:
        return None
    median = sqrt(arg)
    result = middle - line_direction * median

    return result





