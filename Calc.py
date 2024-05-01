'''
geometrical calculations module
'''

from pygame import Vector2
from math import atan2, sqrt, radians, tan

def find_collision_centers_on_line(point: Vector2, point_on_line: Vector2, line_direction: Vector2, radius: float):
    # find distance between line and point. direction must be normalized
    # point - target ball
    # point_on_line - cue ball
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

def closest_point_on_line(point_a: Vector2, point_b: Vector2, point_target: Vector2) -> Vector2:
    ab = point_b - point_a
    ac = point_target - point_a
    if ab.dot(ab) == 0:
        print(1)
    t = ac.dot(ab) / ab.dot(ab)
    if t > 1.0 or t < 0.0:
        return None
    closest_point = point_a + t * ab
    return closest_point

def check_line_circle_collision(point_a: Vector2, point_b: Vector2, circle_center: Vector2, line_radius: float, radius: float) -> bool:
    closest_point = closest_point_on_line(point_a, point_b, circle_center)
    if closest_point is None:
        return False
    if closest_point.distance_to(circle_center) < line_radius + radius:
        return True
    return False

def find_collision_position_ball_to_line(p_a: Vector2, p_b: Vector2, p_c: Vector2, p_d: Vector2, radius: float):
    ### not working
    # p_a to p_b is the line segment 
    # p_c to p_d is the ray
    line1_vec = p_b - p_a
    line2_vec = p_d - p_c

    ray = p_c + (p_d - p_c) * 3000.0

    angle = -radians(line1_vec.angle_to(line2_vec))
    distance_on_line1 = radius / tan(angle)

    # find intersection
    x1, y1 = p_a.x, p_a.y
    x2, y2 = p_b.x, p_b.y
    x3, y3 = p_c.x, p_c.y
    x4, y4 = ray.x, ray.y

    u_nom = (x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)
    u_dem = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if u_dem == 0:
        return None
    u = u_nom / u_dem

    intersection = p_a + u * (line1_vec)
    tangent = intersection - distance_on_line1 * line1_vec.normalize()
    tangent_vec = Vector2(-line1_vec.y, line1_vec.x)
    collision_point = tangent + radius * tangent_vec.normalize()
    return collision_point


