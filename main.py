import pygame
from pygame.locals import *
import sys
from random import randrange
import random
from settings import *
from weapons import *
from pygame.math import Vector2 as Vec
from itertools import cycle

debug_info = True


PLAYER_SPRITE_SIZE = 30


class Hearts(pygame.sprite.Sprite):
    heart_size = 48
    full_heart = pygame.transform.scale(pygame.image.load('sprites/heart_full.png').convert_alpha(), (heart_size, heart_size))
    empty_heart = pygame.transform.scale(pygame.image.load('sprites/heart_empty.png').convert_alpha(), (heart_size, heart_size))

    def update(self, current_number_of_hearts, base_number_of_hearts):
        empty_hearts = base_number_of_hearts - current_number_of_hearts
        start_pos = Vec((0, HEIGHT - self.heart_size))
        for i in range(current_number_of_hearts):
            DISPLAY_SURFACE.blit(self.full_heart, start_pos)
            start_pos.x += self.heart_size
        for i in range(empty_hearts):
            DISPLAY_SURFACE.blit(self.empty_heart, start_pos)
            start_pos.x += self.heart_size


class Player(pygame.sprite.Sprite):
    player_sprite = pygame.transform.scale(pygame.image.load('sprites/player.png').convert_alpha(), (48, 48))
    acceleration = 0.5
    friction = -0.12
    base_hearts = 3
    immunity = 0
    weapons = cycle([Arrow, Axe])

    def __init__(self):
        super().__init__()
        self.image = self.player_sprite
        self.rect = self.image.get_rect(center=(0, 0))

        self.pos = Vec((WIDTH / 2, HEIGHT / 2))
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        self.is_active = True
        self.current_weapon = next(self.weapons)
        self.hearts = self.base_hearts

    def handle_actions(self):
        self.move()
        if self.immunity:
            self.immunity -= 1

    def switch_weapon(self):
        self.current_weapon = next(self.weapons)

    def move(self):
        self.acc = Vec(0, 0)

        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_LEFT] or pressed_keys[K_a]:
            self.acc.x = -self.acceleration
        if pressed_keys[K_RIGHT] or pressed_keys[K_d]:
            self.acc.x = self.acceleration
        if pressed_keys[K_UP] or pressed_keys[K_w]:
            self.acc.y = -self.acceleration
        if pressed_keys[K_DOWN] or pressed_keys[K_s]:
            self.acc.y = self.acceleration

        self.acc += self.vel * self.friction
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        if self.pos.x > WIDTH:
            self.pos.x = WIDTH
        if self.pos.x < 0:
            self.pos.x = 0

        if self.pos.y > HEIGHT + PLAYER_SPRITE_SIZE / 2:
            self.pos.y = HEIGHT + PLAYER_SPRITE_SIZE / 2
        if self.pos.y < 0 + PLAYER_SPRITE_SIZE / 2:
            self.pos.y = 0 + PLAYER_SPRITE_SIZE / 2

        self.rect.midbottom = self.pos

    def kill_player(self):
        print('player is dead')
        self.image, self.rect = rot_center(self.image, 90)
        self.acceleration = 0
        self.is_active = False


class Enemy(pygame.sprite.Sprite):
    enemy_sprite = pygame.transform.scale(pygame.image.load('sprites/ninja.png').convert_alpha(), (48, 48))
    enemy_dead_sprite = pygame.transform.scale(pygame.image.load('sprites/ninja_dead.png').convert_alpha(), (48, 48))

    speed = 1
    base_health = 200

    def __init__(self, position):
        super().__init__()
        self.image = self.enemy_sprite
        self.rect = self.image.get_rect(center=(0, 0))

        self.pos = Vec(position)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)

        self.health = self.base_health
        self.is_active = True

    def show_health_bar(self):
        health_fraction = self. health / self.base_health

        if health_fraction > 0.5:
            bar_color = 'green'
        elif health_fraction > 0.3:
            bar_color = 'yellow'
        else:
            bar_color = 'red'

        bar_left = self.pos.x - self.rect.width / 2
        bar_top = self.pos.y - self.rect.height
        pygame.draw.rect(DISPLAY_SURFACE, pg.color.Color('white'), pygame.Rect(bar_left, bar_top, self.rect.width, 5),  1)
        pygame.draw.rect(DISPLAY_SURFACE, pg.color.Color(bar_color), pygame.Rect(bar_left + 1, bar_top + 1, health_fraction * (self.rect.width - 1), 3))

    def move(self, player_pos):
        if self.is_active:
            vector = self.pos - player_pos
            vector_length = sqrt(vector[0] ** 2 + vector[1] ** 2)
            direction = vector / vector_length
            self.pos -= direction * self.speed
            self.rect.midbottom = self.pos

            self.show_health_bar()

    def check_for_damage(self, sprites):
        for sprite in sprites:
            if isinstance(sprite, Projectile) and self.is_active and sprite.is_active and pygame.sprite.collide_rect(self, sprite):
                self.health -= projectile.damage
                sprite.is_active = False  # TODO: projectile stay in enemy when hit, decrease the bounding box? Projectile should be attached to enemy when he's moving
                if self.health <= 0:
                    self.is_active = False
                    self.image = self.enemy_dead_sprite
                self.rect = self.image.get_rect(center=(0, 0))
                self.rect.midbottom = self.pos
            elif isinstance(sprite, Player) and self.is_active and not sprite.immunity and pygame.sprite.collide_rect(self, sprite) and player.is_active:
                sprite.hearts -= 1
                if sprite.hearts <= 0 and sprite.is_active:
                    sprite.kill_player()
                sprite.immunity = 120


class Crosshair(pygame.sprite.Sprite):
    crosshair_sprite = pygame.image.load('sprites/crosshair.png').convert_alpha()

    def __init__(self):
        super().__init__()
        self.image = self.crosshair_sprite
        self.rect = self.image.get_rect(center=(0, 0))
        self.pos = Vec((WIDTH / 2, HEIGHT / 2))

    def update_position(self, pos):
        self.pos = pos
        self.rect.midbottom = self.pos


def spawn_random_enemy():
    match random.choice([1, 2, 3, 4]):
        case 1:  # top
            return Enemy((randrange(WIDTH), 0))
        case 2:  # right
            return Enemy((WIDTH, randrange(HEIGHT)))
        case 3:  # bottom
            return Enemy((randrange(WIDTH), HEIGHT))
        case 4:  # left
            return Enemy((0, randrange(HEIGHT)))


def display_text(surface, text, pos, font, color=pygame.Color('black')):
    lines = text.splitlines()
    font_height = font.get_height()
    pos_x, pos_y = pos
    for line in lines:
        line_surface = font.render(line, 0, color)
        surface.blit(line_surface, (pos_x, pos_y))
        pos_y += font_height


if __name__ == '__main__':
    FramePerSec = pygame.time.Clock()

    pygame.display.set_caption("game")
    player = Player()
    hearts = Hearts()
    crosshair = Crosshair()

    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    all_sprites.add(crosshair)


    SPAWN_ENEMY_EVERY_N_FRAMES = 60

    frame_number = 0
    while True:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_SPACE:
                    player.switch_weapon()
            elif event.type == MOUSEMOTION:
                crosshair.update_position(event.pos)
            elif event.type == MOUSEBUTTONDOWN:
                weapon_type = player.current_weapon
                projectile = weapon_type(player.pos, event.pos)
                all_sprites.add(projectile)

        DISPLAY_SURFACE.fill(pygame.Color('olivedrab4'))

        if frame_number % SPAWN_ENEMY_EVERY_N_FRAMES == 0:
            enemy = spawn_random_enemy()
            all_sprites.add(enemy)

        player.handle_actions()
        hearts.update(player.hearts, player.base_hearts)

        non_enemy_sprites = [sprite for sprite in all_sprites if not isinstance(sprite, Enemy)]
        for entity in all_sprites:
            if isinstance(entity, Projectile):
                entity.update()
            elif isinstance(entity, Enemy):
                entity.move(player.pos)
                entity.check_for_damage(non_enemy_sprites)
            DISPLAY_SURFACE.blit(entity.image, entity.rect)

        if debug_info:
            text = f'{FramePerSec.get_fps()=}\n' \
                   f'{frame_number=}\n' \
                   f'{player.hearts=}\n' \
                   f'{player.immunity=}\n' \
                   f'{player.pos.x=}\n' \
                   f'{player.pos.y=}\n' \

            display_text(DISPLAY_SURFACE, text, (20, 20), FONT)

        frame_number += 1
        pygame.display.update()
        FramePerSec.tick(FPS)
