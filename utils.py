import pygame as pg
from math import atan2, degrees, pi


def rot_center(image, angle):
    rotated_image = pg.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(center=image.get_rect().center).center)
    return rotated_image, new_rect


def angle_between_vectors(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]
    rads = atan2(-dy, dx)
    rads %= 2 * pi
    return degrees(rads)
