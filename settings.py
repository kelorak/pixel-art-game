import pygame as pg

pg.init()
pg.mouse.set_visible(False)

WIDTH = 1920
HEIGHT = 1080
FPS = 60
SPAWN_ENEMY_EVERY_N_FRAMES = 150
FONT = pg.font.SysFont('consolas', 20, bold=True)
DISPLAY_SURFACE = pg.display.set_mode((WIDTH, HEIGHT))
DEBUG_SHOW_INFO = True
DEBUG_SHOW_BOUNDING_BOX = True
