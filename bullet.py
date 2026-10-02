"""
bullet.py
---------
A very small class for a single projectile. Both the player and the
enemies create Bullet objects; the `owner` field ("player" or "enemy")
tells game.py who it can hurt.
"""

import math
import pygame
from settings import (
    SCREEN_WIDTH, ARENA_TOP, ARENA_BOTTOM,
    COLOR_PLAYER_BULLET, COLOR_ENEMY_BULLET,
)


class Bullet:
    def __init__(self, x, y, target_x, target_y, speed, damage, radius, owner):
        self.x = x
        self.y = y
        self.radius = radius
        self.damage = damage
        self.owner = owner  # "player" or "enemy"
        self.alive = True

        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1  # avoid dividing by zero if fired at own position

        self.vx = (dx / distance) * speed
        self.vy = (dy / distance) * speed

        self.color = COLOR_PLAYER_BULLET if owner == "player" else COLOR_ENEMY_BULLET

    def update(self, walls):
        self.x += self.vx
        self.y += self.vy

        # Remove the bullet once it leaves the arena.
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < ARENA_TOP or self.y > ARENA_BOTTOM:
            self.alive = False
            return

        # Remove the bullet if it hits a wall.
        bullet_rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                   self.radius * 2, self.radius * 2)
        for wall in walls:
            if wall.colliderect(bullet_rect):
                self.alive = False
                return

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
