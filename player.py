"""
player control
"""

import pygame
from settings import (
    PLAYER_RADIUS, PLAYER_SPEED, PLAYER_MAX_HEALTH, PLAYER_SHOOT_COOLDOWN,
    PLAYER_BULLET_SPEED, PLAYER_BULLET_DAMAGE, PLAYER_BULLET_RADIUS,
    COLOR_PLAYER, ARENA_TOP, ARENA_BOTTOM, SCREEN_WIDTH,
)
from bullet import Bullet


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED
        self.max_health = PLAYER_MAX_HEALTH
        self.health = PLAYER_MAX_HEALTH
        self.shoot_timer = 0.0

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def _try_move(self, dx, dy, walls):
        """Move on one axis at a time so sliding along a wall feels natural."""
        new_x = self.x + dx
        new_y = self.y + dy

        # Horizontal movement + wall check
        rect = pygame.Rect(new_x - self.radius, self.y - self.radius,
                            self.radius * 2, self.radius * 2)
        blocked = any(w.colliderect(rect) for w in walls)
        if not blocked:
            self.x = new_x
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))

        # Vertical movement + wall check
        rect = pygame.Rect(self.x - self.radius, new_y - self.radius,
                            self.radius * 2, self.radius * 2)
        blocked = any(w.colliderect(rect) for w in walls)
        if not blocked:
            self.y = new_y
        self.y = max(ARENA_TOP + self.radius, min(ARENA_BOTTOM - self.radius, self.y))

    def handle_input(self, keys, walls):
        """
        Reads WASD keys and moves the player.
        Returns the distance actually traveled this frame (used by
        the AI behavior tracker to measure how much the player moves).
        """
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_s]:
            dy += self.speed
        if keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_d]:
            dx += self.speed

        if dx == 0 and dy == 0:
            return 0.0

        # Prevent diagonal movement from being faster than straight movement.
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        before_x, before_y = self.x, self.y
        self._try_move(dx, dy, walls)
        moved = ((self.x - before_x) ** 2 + (self.y - before_y) ** 2) ** 0.5
        return moved

    def update_timers(self, dt):
        if self.shoot_timer > 0:
            self.shoot_timer -= dt

    def try_shoot(self, target_x, target_y):
        """
        Returns a new Bullet aimed at (target_x, target_y) if the
        cooldown has expired, otherwise returns None.
        """
        if self.shoot_timer > 0:
            return None
        self.shoot_timer = PLAYER_SHOOT_COOLDOWN
        return Bullet(self.x, self.y, target_x, target_y,
                       PLAYER_BULLET_SPEED, PLAYER_BULLET_DAMAGE,
                       PLAYER_BULLET_RADIUS, owner="player")

    def draw(self, surface):
        pygame.draw.circle(surface, COLOR_PLAYER, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

        # small health bar above the player
        bar_w = 36
        bar_h = 5
        ratio = self.health / self.max_health
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.radius - 12
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, (90, 220, 120), (bar_x, bar_y, bar_w * ratio, bar_h))
