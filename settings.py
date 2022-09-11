import pygame as pg
from math import ulp


pg.init()
pg.mouse.set_visible(False)

WIDTH = 1200
HEIGHT = 800
ROWS = 20
COLS = 30
SPRITE_SHEET_ASSET_SIZE = 16
TILE_SIZE = HEIGHT // ROWS
FPS = 60
EPSILON = ulp(1.0)
BACKGROUND_COLOR = pg.Color('olivedrab4')
FONT = pg.font.Font('font/Pixeltype.ttf', 20)
DISPLAY_SURFACE = pg.display.set_mode((WIDTH, HEIGHT))
DEBUG_SHOW_INFO = True
DEBUG_SHOW_BOUNDING_BOX = True
DEBUG_DRAW_GRID = False
