'''
geometrical calculations module
'''

from pygame import Vector2
from math import sqrt, radians, tan

def find_collision_centers_on_line(target_pos: Vector2, cue_pos: Vector2, line_direction: Vector2, radius: float):
    # find distance between line and point. direction must be normalized
    # target_pos - target ball
    # cue_pos - cue ball
    ## calculate line equation m, b
    if line_direction[0] == 0:
        return None
    line_m = line_direction[1] / line_direction[0]  
    line_b = - line_m * cue_pos[0] + cue_pos[1]

    ## calculate line of point
    if line_m == 0:
        return None
    p_line_m = - 1.0 / line_m
    p_line_b = - p_line_m * target_pos[0] + target_pos[1]

    ## find intersection
    x_middle = (p_line_b - line_b) / (line_m - p_line_m)
    y_middle = line_m * x_middle + line_b
    middle = Vector2(x_middle, y_middle)

    ## calculate distance
    distance = middle.distance_to(target_pos)

    # find the points
    arg = 4 * radius * radius - distance * distance
    if arg < 0:
        return None
    median = sqrt(arg)
    ghost_pos = middle - line_direction * median

    cue_to_target = line_direction
    cue_to_ghost = ghost_pos - cue_pos

    if cue_to_target.dot(cue_to_ghost) < 0:
        return None
    return ghost_pos

def closest_point_on_line(point_a: Vector2, point_b: Vector2, point_target: Vector2) -> Vector2:
    # find clsosest point on line ab to target. none if not on line
    ab = point_b - point_a
    ac = point_target - point_a
    if ab.dot(ab) == 0:
        return None
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

def find_collision_position_ball_to_line(p_a: Vector2, p_b: Vector2, p_c: Vector2, p_d: Vector2, ball_radius: float, line_radius: float):
    ### not working
    # p_a to p_b is the line segment 
    # p_c to p_d is the ray
    line1_vec = p_b - p_a
    line2_vec = p_d - p_c

    ray = p_c + (p_d - p_c) * 3000.0

    angle = -radians(line1_vec.angle_to(line2_vec))
    if tan(angle) == 0:
        return None
    
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
    if not 0.0 <= u <= 1.0:
        return None

    intersection = p_a + u * (line1_vec)
    if (p_d - p_c).dot(intersection- p_c) < 1.0:
        return None
    
    # backwards tangent with line radius
    distance_on_line_radius = line_radius / tan(angle)
    tangent_point = intersection + distance_on_line_radius * line1_vec.normalize()
    tangent_vec = Vector2(-line1_vec.y, line1_vec.x)
    collision_point = min([tangent_point + line_radius * tangent_vec.normalize(), tangent_point - line_radius * tangent_vec.normalize()], key=lambda x: x.distance_squared_to(p_c))

    # backwards tangent with ball radius
    distance_on_line_radius = ball_radius / tan(angle)
    tangent_point = collision_point + distance_on_line_radius * line1_vec.normalize()
    tangent_vec = Vector2(-line1_vec.y, line1_vec.x)
    collision_point = min([tangent_point + ball_radius * tangent_vec.normalize(), tangent_point - ball_radius * tangent_vec.normalize()], key=lambda x: x.distance_squared_to(p_c))

    return collision_point


