from math import sqrt

import pygame as pg

from settings import WIDTH, HEIGHT
from utils import angle_between_vectors, rot_center


class Projectile(pg.sprite.Sprite):
    sprite: pg.surface.Surface
    speed: int
    speed_decay: float
    damage: int
    cooldown: int
    knock_back: int

    def __init__(self, origin, destination):
        super().__init__()
        angle = angle_between_vectors(origin, destination)

        self.image, self.rect = rot_center(self.sprite, angle + 90)
        self.pos = origin + (1, 1)
        self.dest = destination
        self.rect.midbottom = self.pos

        vector = origin - destination
        vector_length = sqrt(vector[0] ** 2 + vector[1] ** 2)
        self.direction = vector / vector_length
        self.is_active = True

    def update(self):
        if self.is_active:
            self.pos -= self.direction * self.speed
            self.rect.midbottom = self.pos
            vector = self.pos - self.dest

            self.speed -= self.speed_decay
            if self.speed <= 0:
                self.is_active = False

            distance_from_destination = sqrt(vector[0] ** 2 + vector[1] ** 2)
            if distance_from_destination < 5 or \
                    self.pos.x < 0 or self.pos.x > WIDTH or \
                    self.pos.y < 0 or self.pos.y > HEIGHT:
                self.is_active = False


class Arrow(Projectile):
    sprite = pg.image.load('sprites/arrow.png').convert_alpha()
    speed = 10
    speed_decay = 0.01
    damage = 34
    cooldown = 20
    knock_back = 3


class ThrowingAxe(Projectile):
    sprite = pg.transform.scale(pg.image.load('sprites/axe.png').convert_alpha(), (32, 32))
    speed = 8
    speed_decay = 0.15
    damage = 50
    cooldown = 50
    knock_back = 10
