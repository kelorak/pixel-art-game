import csv
import sys
from itertools import cycle
from math import sqrt, hypot

import psutil
import pygame as pg
from pygame.locals import K_ESCAPE, K_SPACE, MOUSEMOTION, KEYDOWN
from pygame.locals import K_F1, K_F2, K_F3
from pygame.locals import K_UP, K_LEFT, K_DOWN, K_RIGHT
from pygame.locals import K_w, K_a, K_s, K_d
from pygame.math import Vector2 as Vec

from settings import BACKGROUND_COLOR, WIDTH, HEIGHT, TILE_SIZE, SPRITE_SHEET_ASSET_SIZE, DISPLAY_SURFACE, FONT, FPS, EPSILON, FRAMES_PER_ANIMATION_CHANGE  # constants
from settings import DEBUG_SHOW_INFO, DEBUG_SHOW_BOUNDING_BOX, DEBUG_DRAW_GRID  # debug options
from utils import rot_center
from weapons import Projectile, Arrow, ThrowingAxe


def image_at(sheet: pg.surface.Surface, row: int, col: int):
    offset_pixels = 16
    ratio = TILE_SIZE / offset_pixels
    image = pg.Surface((offset_pixels, offset_pixels)).convert_alpha()
    image.blit(sheet, (0, 0), ((col * offset_pixels), row * offset_pixels, offset_pixels, offset_pixels))
    image = pg.transform.scale(image, (offset_pixels * ratio, offset_pixels * ratio))
    image.set_colorkey((0, 0, 0))

    return image


world_sheet = pg.image.load('sprites/Sprite-0001.png').convert_alpha()
img_list = []
rows_count = int(world_sheet.get_height() / SPRITE_SHEET_ASSET_SIZE)
cols_count = int(world_sheet.get_width() / SPRITE_SHEET_ASSET_SIZE)
for row_index in range(rows_count):
    for col_idx in range(cols_count):
        img = image_at(world_sheet, row_index, col_idx)
        img_list.append(img)


class World:
    def __init__(self):
        self.ground_tiles_list = []
        self.obstacle_tiles_list = []

    def process_data(self, data):
        player_object = None
        # Iterate through each value in level data file
        for y, row_data in enumerate(data):
            for x, tile_id in enumerate(row_data):
                if tile_id >= 0:
                    image = img_list[tile_id]
                    img_rect = image.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (image, img_rect)
                    if tile_id == 0:
                        player_object = Player(pos=(x * TILE_SIZE, y * TILE_SIZE))

                        # Add default tile under the player:
                        def_tile_img = img_list[1]
                        img_rect = def_tile_img.get_rect()
                        img_rect.x = x * TILE_SIZE
                        img_rect.y = y * TILE_SIZE
                        tile_data = (def_tile_img, img_rect)
                        self.ground_tiles_list.append(tile_data)
                    elif tile_id == 1:
                        self.ground_tiles_list.append(tile_data)
                    elif tile_id == 5:
                        enemy = Enemy(position=(x * TILE_SIZE, y * TILE_SIZE))
                        # Add default tile under the enemy:
                        def_tile_img = img_list[1]
                        img_rect = def_tile_img.get_rect()
                        img_rect.x = x * TILE_SIZE
                        img_rect.y = y * TILE_SIZE
                        tile_data = (def_tile_img, img_rect)
                        self.ground_tiles_list.append(tile_data)
                        all_sprites.add(enemy)
                    elif 2 <= tile_id <= 15:
                        self.obstacle_tiles_list.append(tile_data)
        assert player_object is not None
        return player_object

    def draw(self):
        for t in self.ground_tiles_list + self.obstacle_tiles_list:
            DISPLAY_SURFACE.blit(t[0], t[1].topleft - offset)


class Hearts(pg.sprite.Sprite):
    full_heart = pg.transform.scale(pg.image.load('sprites/heart_full.png').convert_alpha(), (TILE_SIZE, TILE_SIZE))
    empty_heart = pg.transform.scale(pg.image.load('sprites/heart_empty.png').convert_alpha(), (TILE_SIZE, TILE_SIZE))

    def update(self):
        self.image = pg.Surface((TILE_SIZE * player.base_hearts, TILE_SIZE))
        self.image.set_colorkey(pg.color.Color('black'))

        empty_hearts = player.base_hearts - player.hearts
        start_pos = Vec((0, 0))
        for _ in range(player.hearts):
            self.image.blit(self.full_heart, start_pos)
            start_pos.x += TILE_SIZE
        for _ in range(empty_hearts):
            self.image.blit(self.empty_heart, start_pos)
            start_pos.x += TILE_SIZE
        self.rect = self.image.get_rect()
        self.rect.center = (0, HEIGHT - TILE_SIZE)


class Player(pg.sprite.Sprite):
    # TODO: all these images should be loaded from sprite sheet:
    player_idle_sprite_right = [pg.transform.scale(pg.image.load('sprites/player1.png').convert_alpha(), (TILE_SIZE, TILE_SIZE)),
                                pg.transform.scale(pg.image.load('sprites/player2.png').convert_alpha(), (TILE_SIZE, TILE_SIZE)),
                                pg.transform.scale(pg.image.load('sprites/player3.png').convert_alpha(), (TILE_SIZE, TILE_SIZE)),
                                pg.transform.scale(pg.image.load('sprites/player4.png').convert_alpha(), (TILE_SIZE, TILE_SIZE))]
    player_idle_sprite_left = [pg.transform.flip(x.copy(), True, False) for x in player_idle_sprite_right]
    player_walking_sprite_right = player_idle_sprite_right  # TODO: change when animation for walking available
    player_walking_sprite_left = player_idle_sprite_left  # TODO: change when animation for walking available

    player_idle_sprite_right = cycle(player_idle_sprite_right)
    player_idle_sprite_left = cycle(player_idle_sprite_left)
    player_walking_sprite_right = cycle(player_walking_sprite_right)
    player_walking_sprite_left = cycle(player_walking_sprite_left)

    acceleration = 0.5
    friction = -0.12
    base_hearts = 3
    immunity_frames_after_hit = 120
    weapons = cycle([Arrow, ThrowingAxe])

    def __init__(self, pos):
        super().__init__()
        self.image = next(self.player_idle_sprite_right)
        self.rect = self.image.get_rect()
        self.pos = Vec(pos)
        self.rect.topleft = pos
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        self.immunity = 0
        self.is_active = True
        self.current_weapon = next(self.weapons)
        self.weapon_cooldown = 0
        self.hearts = self.base_hearts
        self.dx = 0
        self.dy = 0

    def update(self):
        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE:
                self.switch_weapon()
        if pg.mouse.get_pressed()[0] and not self.weapon_cooldown:
            self.attack()
        self.apply_appropriate_image()
        self.move()
        if self.immunity:
            self.immunity -= 1
        if self.weapon_cooldown:
            self.weapon_cooldown -= 1

    def attack(self):
        weapon_type = self.current_weapon
        mouse_pos = Vec(pg.mouse.get_pos())
        projectile = weapon_type(self.pos, mouse_pos + offset, max_x, max_y)
        self.weapon_cooldown = weapon_type.cooldown
        all_sprites.add(projectile)

    def apply_appropriate_image(self):
        animation_frame_time = 300
        frame_update_count = int(animation_frame_time / (1000 / FPS))
        if abs(self.vel.x) > 0.5 or abs(self.vel.y) > 0.5:
            if FRAME_NUMBER % int(10 / self.acceleration) == 0:
                if self.vel.x >= 0:
                    self.image = next(self.player_walking_sprite_right)
                else:
                    next(self.player_walking_sprite_left)
        elif FRAME_NUMBER % frame_update_count == 0:
            self.image = next(self.player_idle_sprite_right) if self.vel.x >= 0 else next(self.player_idle_sprite_left)

    def switch_weapon(self):
        self.current_weapon = next(self.weapons)

    def check_collision_with_world_boundary(self):
        # Check for collision with screen boundaries - sanity check, it should be handled by level map design
        if self.pos.x > max_x:
            self.pos.x = max_x
        elif self.pos.x < 0:
            self.pos.x = 0
        if self.pos.y > max_y:
            self.pos.y = max_y
        elif self.pos.y < 0:
            self.pos.y = 0

    def move(self):
        self.acc = Vec(0, 0)

        pressed_keys = pg.key.get_pressed()
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
        dx, dy = self.vel + 0.5 * self.acc

        self.check_collision_with_world_boundary()

        # Check for collision with obstacles
        shrunk_tile_ratio = 0.75  # compare rect collision with smaller tile for smoother movement near narrow passages
        shrunk_tile_size = (shrunk_tile_ratio * TILE_SIZE)
        shrunk_tile_offset = (((1 - shrunk_tile_ratio) / 2) * TILE_SIZE)
        # TODO: filter out tile list to check colliderect only with tiles adjacent to player
        for t in world.obstacle_tiles_list:
            if t[1].colliderect(self.pos.x + dx + shrunk_tile_offset, self.pos.y + shrunk_tile_offset, shrunk_tile_size, shrunk_tile_size):
                dx = 0
                self.vel.x = 0
                self.acc.x = 0
            if t[1].colliderect(self.pos.x + shrunk_tile_offset, self.pos.y + shrunk_tile_offset + dy, shrunk_tile_size, shrunk_tile_size):
                dy = 0
                self.vel.y = 0
                self.acc.y = 0
        self.pos += dx, dy
        self.rect.center = self.pos
        self.dx = dx
        self.dy = dy

    def kill_player(self):
        self.image, self.rect = rot_center(self.image, 90)
        self.acceleration = EPSILON  # TODO: why didn't I set it to zero? To check
        self.is_active = False


class Enemy(pg.sprite.Sprite):
    base_speed = 0.5
    base_health = 100
    sight = 4

    action_idle = 0
    action_move = 1
    action_attack = 2
    action_die = 3

    def __init__(self, position):
        enemy_idle_sprite_sheet = pg.image.load('sprites/enemy_standing_front.png').convert_alpha()
        enemy_walking_sprite_sheet = pg.image.load('sprites/enemy_walking.png').convert_alpha()
        enemy_attack_sprite_sheet = pg.image.load('sprites/enemy_attack.png').convert_alpha()
        self.enemy_idle_animation = cycle([image_at(enemy_idle_sprite_sheet, 0, i) for i in range(3)])
        self.enemy_move_left_animation = cycle([image_at(enemy_walking_sprite_sheet, 0, i) for i in range(5)])
        self.enemy_move_right_animation = cycle([pg.transform.flip(image_at(enemy_walking_sprite_sheet, 0, i), True, False).convert_alpha() for i in range(5)])
        self.enemy_attack_left_animation = cycle(reversed([image_at(enemy_attack_sprite_sheet, 0, i) for i in range(4)]))
        self.enemy_attack_right_animation = cycle(reversed([pg.transform.flip(image_at(enemy_attack_sprite_sheet, 0, i), True, False).convert_alpha() for i in range(4)]))

        super().__init__()
        self.image = next(self.enemy_idle_animation)
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        self.pos = Vec(position)
        self.direction = Vec(0, 0)

        self.health = self.base_health
        self.speed = self.base_speed
        self.is_active = True
        self.action = self.action_idle

    def apply_appropriate_image(self):
        if not self.is_active:  # add animation for dead enemy
            self.image = next(self.enemy_idle_animation)
        elif self.action == self.action_idle:
            if FRAME_NUMBER % FRAMES_PER_ANIMATION_CHANGE == 0:
                self.image = next(self.enemy_idle_animation) if self.direction.x > 0 else next(self.enemy_idle_animation)
        elif self.action == self.action_move:
            if FRAME_NUMBER % FRAMES_PER_ANIMATION_CHANGE == 0:
                if self.direction.x < 0:
                    self.image = next(self.enemy_move_right_animation)
                else:
                    next(self.enemy_move_left_animation)
        elif self.action == self.action_attack:
            if FRAME_NUMBER % FRAMES_PER_ANIMATION_CHANGE == 0:
                if self.direction.x < 0:
                    self.image = next(self.enemy_attack_right_animation)
                else:
                    next(self.enemy_attack_left_animation)
        elif self.action == self.action_die:
            self.kill()

    def update(self):
        self.update_action()
        self.apply_appropriate_image()
        self.move()
        self.check_for_damage()
        self.show_health_bar()

    def update_action(self):
        distance_from_player = hypot(self.pos.x - player.pos.x, self.pos.y - player.pos.y)
        if distance_from_player < TILE_SIZE:
            self.action = self.action_attack
        elif distance_from_player < TILE_SIZE * self.sight:
            self.action = self.action_move
        else:
            self.action = self.action_idle

    def show_health_bar(self):
        health_fraction = self. health / self.base_health

        if health_fraction > 0.5:
            bar_color = 'green'
        elif health_fraction > 0.3:
            bar_color = 'yellow'
        else:
            bar_color = 'red'

        bar_left = self.pos.x + self.rect.width / 2 - offset.x
        bar_top = self.pos.y + self.rect.height / 4 - offset.y
        pg.draw.rect(DISPLAY_SURFACE,
                     pg.color.Color('black'),
                     pg.Rect(bar_left, bar_top, self.rect.width + 1, 5),
                     1)
        pg.draw.rect(DISPLAY_SURFACE,
                     pg.color.Color(bar_color),
                     pg.Rect(bar_left + 1, bar_top + 1, health_fraction * (self.rect.width - 1), 3))

    def move(self):
        if self.is_active and self.action != self.action_idle:
            vector = self.pos - player.pos
            vector_length = sqrt(vector[0] ** 2 + vector[1] ** 2)
            self.direction = vector / vector_length
            self.pos -= self.direction * self.speed
            self.rect.topleft = self.pos
            # TODO: check if speed regain after knock back should be parametrized based on enemy size/weight
            speed_regain_ratio = 0.1
            self.speed += (self.base_speed - self.speed) * speed_regain_ratio

    def check_for_damage(self):
        for sprite in all_sprites:
            if isinstance(sprite, Projectile) \
                    and self.is_active \
                    and sprite.is_active \
                    and pg.sprite.collide_rect(self, sprite):
                self.speed -= sprite.knock_back
                self.health -= sprite.damage
                # TODO: projectile stay in enemy when hit, decrease the bounding box?
                #  Projectile should be attached to enemy when he's moving
                sprite.is_active = False
                if self.health <= 0:
                    self.is_active = False
            elif isinstance(sprite, Player) \
                    and self.is_active \
                    and not sprite.immunity \
                    and pg.sprite.collide_rect(self, sprite) \
                    and player.is_active:
                sprite.hearts -= 1
                if sprite.hearts <= 0 and sprite.is_active:
                    sprite.kill_player()
                sprite.immunity = Player.immunity_frames_after_hit


class Crosshair(pg.sprite.Sprite):
    crosshair_sprite = pg.image.load('sprites/crosshair.png').convert_alpha()

    def __init__(self):
        super().__init__()
        self.image = self.crosshair_sprite
        self.rect = self.image.get_bounding_rect()
        self.pos = (0, 0)

    def update(self):
        for e in events:
            if e.type == MOUSEMOTION:
                self.pos = e.pos
                self.rect.center = self.pos


def display_debug_text(surface, pos, font, font_color=pg.Color('black')):
    text = f'{FramePerSec.get_fps()=}\n' \
           f'{FRAME_NUMBER=}\n' \
           f'{player.hearts=}\n' \
           f'{player.immunity=}\n' \
           f'{player.weapon_cooldown=}\n' \
           f'{player.pos.x=}\n' \
           f'{player.pos.y=}\n' \
           f'{player.acc=}\n' \
           f'{player.vel=}\n' \
           f'{ram_usage=}%\n' \
           f'{cpu_usage=}%\n' \
           f'{offset=}\n'
    lines = text.splitlines()
    font_height = font.get_height()
    pos_x, pos_y = pos
    for line in lines:
        line_surface = font.render(line, False, font_color)
        surface.blit(line_surface, (pos_x, pos_y))
        pos_y += font_height


def draw_grid():
    block_size = TILE_SIZE
    for x in range(0, WIDTH, block_size):
        for y in range(0, HEIGHT, block_size):
            rect = pg.Rect(x - 1, y - 1, block_size + 1, block_size + 1)
            pg.draw.rect(DISPLAY_SURFACE, pg.color.Color('magenta'), rect, 1)


def draw_bounding_boxes():
    for sprite in all_sprites:
        if hasattr(sprite, 'is_active'):
            bounding_box_color = 'green' if sprite.is_active else 'red'
            rect_to_draw = sprite.rect.copy()
            rect_to_draw.x -= offset.x - TILE_SIZE / 2
            rect_to_draw.y -= offset_y - TILE_SIZE / 2
            pg.draw.rect(DISPLAY_SURFACE, pg.color.Color(bounding_box_color), rect_to_draw, 1)
            if isinstance(sprite, Enemy):
                pg.draw.circle(DISPLAY_SURFACE,
                               pg.color.Color('blue'),
                               sprite.rect.bottomright - offset,
                               TILE_SIZE * sprite.sight,
                               1)
                if not sprite.action == sprite.action_idle:
                    sight_spotted_line_offset = offset - Vec(TILE_SIZE / 2, TILE_SIZE / 2)
                    pg.draw.aaline(DISPLAY_SURFACE,
                                   pg.color.Color('orange'),
                                   sprite.rect.center - sight_spotted_line_offset,
                                   player.rect.center - sight_spotted_line_offset,
                                   1)


def load_world_data(level_csv: str) -> list:
    output = []

    with open(level_csv, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row_idx, level_row in enumerate(reader):
            output.append([])
            for tile in level_row:
                output[row_idx].append(int(tile))
    return output


if __name__ == '__main__':
    FramePerSec = pg.time.Clock()

    pg.display.set_caption('game')

    world_data = load_world_data('level1.csv')
    max_x = (len(world_data[0]) - 1) * TILE_SIZE
    max_y = (len(world_data) - 1) * TILE_SIZE

    all_sprites = pg.sprite.Group()
    world = World()
    player = world.process_data(world_data)

    all_sprites.add(player)
    all_sprites.add(Crosshair())
    all_sprites.add(Hearts())

    FRAME_NUMBER = 0
    while True:
        events = pg.event.get()
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pg.quit()
                    sys.exit()
                elif event.key == K_F1:
                    DEBUG_SHOW_INFO = not DEBUG_SHOW_INFO
                elif event.key == K_F2:
                    DEBUG_SHOW_BOUNDING_BOX = not DEBUG_SHOW_BOUNDING_BOX
                elif event.key == K_F3:
                    DEBUG_DRAW_GRID = not DEBUG_DRAW_GRID

        DISPLAY_SURFACE.fill(BACKGROUND_COLOR)
        offset_x = player.rect.centerx - (DISPLAY_SURFACE.get_width() // 2)
        offset_y = player.rect.centery - (DISPLAY_SURFACE.get_height() // 2)

        offset = Vec(offset_x, offset_y)
        world.draw()

        if DEBUG_DRAW_GRID:
            draw_grid()

        for s in all_sprites:
            s.update()
            position_to_draw = s.rect.center
            if not isinstance(s, Crosshair) and not isinstance(s, Hearts):
                position_to_draw -= offset
            DISPLAY_SURFACE.blit(s.image, position_to_draw)

        if DEBUG_SHOW_BOUNDING_BOX:
            draw_bounding_boxes()
        if DEBUG_SHOW_INFO:
            if FRAME_NUMBER % 30 == 0:
                ram_usage = round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total, 2)
                cpu_usage = psutil.cpu_percent()
            display_debug_text(DISPLAY_SURFACE, (20, 20), FONT)
        FRAME_NUMBER += 1
        pg.display.update()
        FramePerSec.tick(FPS)
