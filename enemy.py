"""
enemy.py
--------
Enemies are controlled by a genuine Finite State Machine (FSM):

    PATROL --(player detected)--> CHASE
    CHASE  --(player in range)--> ATTACK
    ATTACK --(health low)------->  RETREAT
    (any)  --(health low)------->  RETREAT

Movement toward the player uses real A* pathfinding (see pathfinding.py)
so enemies walk around walls instead of through them.

The *strategy* set by ai.py ("RUSH", "SURROUND", "KEEP_DISTANCE") does
NOT replace the FSM - it changes WHERE an enemy tries to stand while it
is in the CHASE / ATTACK states. This is what makes the adaptation
visible: the same states are used, but the enemies end up positioning
themselves differently once the AI adapts.
"""

import math
import random
import pygame

from settings import (
    ENEMY_RADIUS, ENEMY_MAX_HEALTH, ENEMY_LOW_HEALTH_RATIO,
    ENEMY_DETECTION_RADIUS, ENEMY_CONTACT_DAMAGE, ENEMY_CONTACT_COOLDOWN,
    ENEMY_BULLET_SPEED, ENEMY_BULLET_DAMAGE, ENEMY_BULLET_RADIUS,
    ENEMY_SHOOT_COOLDOWN, ATTACK_RADIUS, ENEMY_SPEED,
    SURROUND_RADIUS, KEEP_DISTANCE_RING,
    SCREEN_WIDTH, ARENA_TOP, ARENA_BOTTOM,
    COLOR_CHASER, COLOR_SHOOTER, COLOR_FLANKER, COLOR_TEXT,
    PATH_RECALC_FRAMES,
)
from pathfinding import world_to_grid, grid_to_world, astar
from bullet import Bullet

ROLE_COLORS = {
    "chaser": COLOR_CHASER,
    "shooter": COLOR_SHOOTER,
    "flanker": COLOR_FLANKER,
}


def _distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


class Enemy:
    def __init__(self, x, y, role, enemy_index, total_enemies):
        self.x = x
        self.y = y
        self.spawn_x = x
        self.spawn_y = y
        self.role = role
        self.enemy_index = enemy_index      # used to spread enemies out when surrounding
        self.total_enemies = max(total_enemies, 1)

        self.radius = ENEMY_RADIUS
        self.max_health = ENEMY_MAX_HEALTH
        self.health = ENEMY_MAX_HEALTH
        self.speed = ENEMY_SPEED[role]
        self.attack_radius = ATTACK_RADIUS[role]
        self.detection_radius = ENEMY_DETECTION_RADIUS

        self.state = "PATROL"
        self.strategy = "RUSH"  # updated externally by the AI controller

        # patrol behaviour
        self.patrol_target = self._new_patrol_point()

        # A* path following
        self.path = []
        self.path_timer = 0

        # attack timers
        self.contact_timer = 0.0
        self.shoot_timer = random.uniform(0, ENEMY_SHOOT_COOLDOWN)

        # slow rotation used by the SURROUND strategy so enemies drift
        # around the player instead of standing frozen in one spot
        self.orbit_offset = random.uniform(0, math.tau)

        self.alive = True

    # -----------------------------------------------------------
    # FSM
    # -----------------------------------------------------------
    def _update_state(self, player_dist):
        if self.health <= self.max_health * ENEMY_LOW_HEALTH_RATIO:
            self.state = "RETREAT"
        elif player_dist <= self.attack_radius:
            self.state = "ATTACK"
        elif player_dist <= self.detection_radius:
            self.state = "CHASE"
        else:
            self.state = "PATROL"

    # -----------------------------------------------------------
    # Strategy-aware target selection
    # -----------------------------------------------------------
    def _chase_target(self, player):
        """Decide WHERE this enemy wants to stand, based on the current strategy."""
        if self.strategy == "RUSH":
            return player.x, player.y

        if self.strategy == "SURROUND":
            # Spread enemies evenly around the player, slowly rotating.
            angle = self.orbit_offset + (2 * math.pi * self.enemy_index / self.total_enemies)
            tx = player.x + math.cos(angle) * SURROUND_RADIUS
            ty = player.y + math.sin(angle) * SURROUND_RADIUS
            return tx, ty

        if self.strategy == "KEEP_DISTANCE":
            dist = _distance(self.x, self.y, player.x, player.y)
            if dist < KEEP_DISTANCE_RING:
                # back away from the player
                angle = math.atan2(self.y - player.y, self.x - player.x)
                tx = player.x + math.cos(angle) * KEEP_DISTANCE_RING
                ty = player.y + math.sin(angle) * KEEP_DISTANCE_RING
                return tx, ty
            else:
                return player.x, player.y

        return player.x, player.y

    # -----------------------------------------------------------
    # Movement helpers
    # -----------------------------------------------------------
    def _move_towards_point(self, tx, ty, walls, speed=None):
        speed = self.speed if speed is None else speed
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        dx, dy = dx / dist, dy / dist
        step = min(speed, dist)

        new_x = self.x + dx * step
        new_y = self.y + dy * step

        rect = pygame.Rect(new_x - self.radius, self.y - self.radius,
                            self.radius * 2, self.radius * 2)
        if not any(w.colliderect(rect) for w in walls):
            self.x = new_x
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))

        rect = pygame.Rect(self.x - self.radius, new_y - self.radius,
                            self.radius * 2, self.radius * 2)
        if not any(w.colliderect(rect) for w in walls):
            self.y = new_y
        self.y = max(ARENA_TOP + self.radius, min(ARENA_BOTTOM - self.radius, self.y))

    def _follow_path_towards(self, tx, ty, grid, walls):
        """Use A* to get a path to (tx, ty) and step along it."""
        self.path_timer -= 1
        goal_cell = world_to_grid(tx, ty)

        need_new_path = (
            self.path_timer <= 0
            or not self.path
        )
        if need_new_path:
            start_cell = world_to_grid(self.x, self.y)
            self.path = astar(grid, start_cell, goal_cell)
            self.path_timer = PATH_RECALC_FRAMES

        if self.path:
            next_col, next_row = self.path[0]
            next_x, next_y = grid_to_world(next_col, next_row)
            self._move_towards_point(next_x, next_y, walls)
            if _distance(self.x, self.y, next_x, next_y) < self.speed + 2:
                self.path.pop(0)
        else:
            # No path found (e.g. fully boxed in) - fall back to a direct nudge.
            self._move_towards_point(tx, ty, walls)

    def _new_patrol_point(self):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(40, 110)
        px = self.spawn_x + math.cos(angle) * radius
        py = self.spawn_y + math.sin(angle) * radius
        px = max(20, min(SCREEN_WIDTH - 20, px))
        py = max(ARENA_TOP + 20, min(ARENA_BOTTOM - 20, py))
        return px, py

    # -----------------------------------------------------------
    # Main update
    # -----------------------------------------------------------
    def update(self, dt, player, walls, grid):
        """
        Returns a new Bullet if this enemy fired one this frame,
        otherwise returns None.
        """
        player_dist = _distance(self.x, self.y, player.x, player.y)
        self._update_state(player_dist)

        fired_bullet = None

        if self.state == "PATROL":
            self._move_towards_point(self.patrol_target[0], self.patrol_target[1], walls, speed=self.speed * 0.6)
            if _distance(self.x, self.y, self.patrol_target[0], self.patrol_target[1]) < 8:
                self.patrol_target = self._new_patrol_point()

        elif self.state == "CHASE":
            tx, ty = self._chase_target(player)
            self._follow_path_towards(tx, ty, grid, walls)

        elif self.state == "ATTACK":
            if self.role == "shooter":
                # hold roughly at attack range and shoot
                if player_dist < self.attack_radius - 20:
                    angle = math.atan2(self.y - player.y, self.x - player.x)
                    tx = self.x + math.cos(angle) * 30
                    ty = self.y + math.sin(angle) * 30
                    self._move_towards_point(tx, ty, walls)
                self.shoot_timer -= dt
                if self.shoot_timer <= 0:
                    self.shoot_timer = ENEMY_SHOOT_COOLDOWN
                    fired_bullet = Bullet(self.x, self.y, player.x, player.y,
                                           ENEMY_BULLET_SPEED, ENEMY_BULLET_DAMAGE,
                                           ENEMY_BULLET_RADIUS, owner="enemy")
            else:
                # chaser / flanker: close in and deal contact damage
                tx, ty = self._chase_target(player)
                self._move_towards_point(tx, ty, walls)
                self.contact_timer -= dt
                if player_dist <= self.attack_radius and self.contact_timer <= 0:
                    self.contact_timer = ENEMY_CONTACT_COOLDOWN
                    player.take_damage(ENEMY_CONTACT_DAMAGE)

        elif self.state == "RETREAT":
            angle = math.atan2(self.y - player.y, self.x - player.x)
            tx = self.x + math.cos(angle) * 60
            ty = self.y + math.sin(angle) * 60
            self._move_towards_point(tx, ty, walls, speed=self.speed * 1.2)

        return fired_bullet

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
            return True
        return False

    def draw(self, surface, font, debug_mode):
        color = ROLE_COLORS[self.role]
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (20, 20, 20), (int(self.x), int(self.y)), self.radius, 2)

        # health bar
        bar_w = 32
        bar_h = 4
        ratio = max(0, self.health / self.max_health)
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.radius - 10
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 90, 90), (bar_x, bar_y, bar_w * ratio, bar_h))

        if debug_mode:
            label = f"{self.role[:2].upper()}:{self.state}"
            text_surf = font.render(label, True, COLOR_TEXT)
            surface.blit(text_surf, (self.x - text_surf.get_width() // 2, self.y + self.radius + 4))
