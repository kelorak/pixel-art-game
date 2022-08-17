import pygame as pg


WIDTH = 1920
HEIGHT = 1080
FPS = 60

pg.init()
DISPLAY_SURFACE = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
FONT = pg.font.Font('freesansbold.ttf', 16)
pg.mouse.set_visible(False)
