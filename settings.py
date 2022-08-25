import pygame as pg
from math import ulp


pg.init()
pg.mouse.set_visible(False)

WIDTH = 1920
HEIGHT = 1080
FPS = 60
EPSILON = ulp(1.0)
ENEMY_SPAWN_TIME = 3000
ENEMY_SPAWN_EVENT = pg.USEREVENT + 1
BACKGROUND_COLOR = pg.Color('olivedrab4')
FONT = pg.font.Font('font/Pixeltype.ttf', 40)
DISPLAY_SURFACE = pg.display.set_mode((WIDTH, HEIGHT))
DEBUG_SHOW_INFO = True
DEBUG_SHOW_BOUNDING_BOX = True
DEBUG_DRAW_GRID = False
