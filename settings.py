import pygame as pg


WIDTH = 1920
HEIGHT = 1080
FPS = 60
SPAWN_ENEMY_EVERY_N_FRAMES = 150

pg.init()
DISPLAY_SURFACE = pg.display.set_mode((WIDTH, HEIGHT))
FONT = pg.font.Font('freesansbold.ttf', 16)
pg.mouse.set_visible(False)
