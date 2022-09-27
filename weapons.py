from math import sqrt

import pygame as pg

from settings import WIDTH, HEIGHT, TILE_SIZE
from utils import angle_between_vectors, rot_center


class Projectile(pg.sprite.Sprite):
    sprite: pg.surface.Surface
    speed: int
    speed_decay: float
    damage: int
    cooldown: int
    knock_back: int

    def __init__(self, origin, destination, max_x, max_y):
        super().__init__()
        angle = angle_between_vectors(origin, destination)

        self.image, self.rect = rot_center(self.sprite, angle + 90)
        self.rect.x += self.rect.width
        self.rect.y += self.rect.height
        self.rect.width *= 0.5
        self.rect.height *= 0.5
        self.pos = origin + (1, 1)
        self.dest = destination
        self.rect.center = self.pos

        vector = origin - destination
        vector_length = sqrt(vector[0] ** 2 + vector[1] ** 2)
        self.direction = vector / vector_length
        self.is_active = True
        self.max_x = max_x
        self.max_y = max_y

    def update(self):
        if self.is_active:
            self.pos -= self.direction * self.speed
            self.rect.center = self.pos

            self.speed -= self.speed_decay
            if self.speed <= 0:
                self.is_active = False

            # Stop the projectile when it flies out of the field of view:
            if self.pos.x < -WIDTH / 2 or \
                    self.pos.x > self.max_x + WIDTH / 2 or \
                    self.pos.y < -HEIGHT / 2 or \
                    self.pos.y > self.max_y + HEIGHT / 2:
                self.is_active = False


class Arrow(Projectile):
    sprite = pg.transform.scale(pg.image.load('sprites/arrow.png').convert_alpha(), (TILE_SIZE, TILE_SIZE))
    speed = 20
    speed_decay = 0.12
    damage = 34
    cooldown = 50
    knock_back = 3


class ThrowingAxe(Projectile):
    sprite = pg.transform.scale(pg.image.load('sprites/axe.png').convert_alpha(), (TILE_SIZE, TILE_SIZE))
    speed = 10
    speed_decay = 0.15
    damage = 50
    cooldown = 80
    knock_back = 10
