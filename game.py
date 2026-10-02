"""
game.py
-------
The Game class owns everything: the current game state, the level
number, the player, the enemies, the bullets, the AI controller and
the on-screen dashboard. main.py just creates a Game and calls run().

GAME STATES
    MENU            -> title screen, press ENTER to start
    GAMEPLAY        -> normal level play
    LEVEL_COMPLETE  -> brief "LEVEL X COMPLETE" banner (auto-advances)
    AI_ANALYSIS     -> shows player classification + new strategy, waits for ENTER
    FINAL_BATTLE    -> final fight, AI learning is OFF
    FINAL_DASHBOARD -> end-of-game AI performance report
    GAME_OVER       -> player died, press ENTER to return to MENU
"""

import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, UI_HEIGHT, FPS,
    ARENA_TOP, ARENA_BOTTOM,
    COLOR_BG, COLOR_ARENA_BG, COLOR_UI_BG, COLOR_WALL, COLOR_TEXT,
    COLOR_TEXT_DIM, COLOR_ACCENT, COLOR_GOOD, COLOR_BAD, COLOR_WARN,
    LEVEL_ENEMY_COUNTS, FINAL_BATTLE_ENEMY_COUNT, TOTAL_LEARNING_LEVELS,
    DEBUG_MODE,
)
from pathfinding import build_grid
from player import Player
from enemy import Enemy
from ai import PlayerStats, AIController


def build_walls():
    """
    One fixed arena layout (no procedural generation), built as a list
    of pygame.Rect. Roughly mirrors the ASCII map in the design doc.
    """
    return [
        pygame.Rect(120, ARENA_TOP + 70, 110, 34),
        pygame.Rect(770, ARENA_TOP + 70, 110, 34),
        pygame.Rect(445, ARENA_TOP + 180, 110, 34),
        pygame.Rect(90, ARENA_TOP + 330, 110, 34),
        pygame.Rect(800, ARENA_TOP + 330, 110, 34),
        pygame.Rect(445, ARENA_TOP + 440, 110, 34),
    ]


SPAWN_POINTS = [
    (60, ARENA_TOP + 40), (SCREEN_WIDTH - 60, ARENA_TOP + 40),
    (60, ARENA_BOTTOM - 40), (SCREEN_WIDTH - 60, ARENA_BOTTOM - 40),
    (SCREEN_WIDTH // 2, ARENA_TOP + 30), (SCREEN_WIDTH // 2, ARENA_BOTTOM - 30),
]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EvoArena - Adaptive 2D Battle Arena")
        self.clock = pygame.time.Clock()

        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 44)
        self.font_title = pygame.font.Font(None, 64)

        self.walls = build_walls()
        self.grid = build_grid(self.walls)

        self.debug_mode = DEBUG_MODE
        self.running = True

        self.reset_game()

    # -----------------------------------------------------------
    # Setup / reset
    # -----------------------------------------------------------
    def reset_game(self):
        self.state = "MENU"
        self.current_level = 0
        self.player = Player(SCREEN_WIDTH // 2, (ARENA_TOP + ARENA_BOTTOM) // 2)
        self.enemies = []
        self.bullets = []
        self.stats = PlayerStats()
        self.ai = AIController()

        # totals shown on the final dashboard (persist across all levels)
        self.total_bullets_fired = 0
        self.total_kills = 0

        self.completion_timer = 0.0
        self.completion_message = ""
        self.next_state_after_completion = "AI_ANALYSIS"

        self.analysis_player_type = None
        self.analysis_scores = {}
        self.analysis_previous_strategy = self.ai.strategy
        self.analysis_new_strategy = self.ai.strategy
        self.analysis_is_final = False

    def spawn_enemies(self, chasers, shooters, flankers):
        self.enemies = []
        roles = ["chaser"] * chasers + ["shooter"] * shooters + ["flanker"] * flankers
        random.shuffle(roles)
        points = SPAWN_POINTS[:]
        random.shuffle(points)

        for i, role in enumerate(roles):
            px, py = points[i % len(points)]
            enemy = Enemy(px, py, role, enemy_index=i, total_enemies=len(roles))
            enemy.strategy = self.ai.strategy
            self.enemies.append(enemy)

    def start_level(self, level_number):
        self.current_level = level_number
        self.bullets = []
        self.stats.reset()
        self.player.health = self.player.max_health

        if level_number <= TOTAL_LEARNING_LEVELS:
            chasers, shooters, flankers = LEVEL_ENEMY_COUNTS[level_number]
        else:
            chasers, shooters, flankers = FINAL_BATTLE_ENEMY_COUNT

        self.spawn_enemies(chasers, shooters, flankers)
        self.state = "GAMEPLAY" if level_number <= TOTAL_LEARNING_LEVELS else "FINAL_BATTLE"

    def start_completion_banner(self, message, next_state):
        self.completion_timer = 1.3
        self.completion_message = message
        self.next_state_after_completion = next_state
        self.state = "LEVEL_COMPLETE"

    # -----------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN:
                    self._handle_enter()
                elif event.key == pygame.K_SPACE and self.state in ("GAMEPLAY", "FINAL_BATTLE"):
                    self._player_shoot()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state in ("GAMEPLAY", "FINAL_BATTLE"):
                    self._player_shoot()

    def _handle_enter(self):
        if self.state == "MENU":
            self.start_level(1)

        elif self.state == "AI_ANALYSIS":
            if self.analysis_is_final:
                self.start_level(TOTAL_LEARNING_LEVELS + 1)  # final battle
            else:
                self.start_level(self.current_level + 1)

        elif self.state == "FINAL_DASHBOARD":
            self.reset_game()

        elif self.state == "GAME_OVER":
            self.reset_game()

    def _player_shoot(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        bullet = self.player.try_shoot(mouse_x, mouse_y)
        if bullet:
            self.bullets.append(bullet)
            self.stats.record_shot()
            self.total_bullets_fired += 1

    # -----------------------------------------------------------
    # Update
    # -----------------------------------------------------------
    def _update(self, dt):
        if self.state in ("GAMEPLAY", "FINAL_BATTLE"):
            self._update_gameplay(dt)
        elif self.state == "LEVEL_COMPLETE":
            self.completion_timer -= dt
            if self.completion_timer <= 0:
                self._enter_next_state()

    def _enter_next_state(self):
        if self.next_state_after_completion == "AI_ANALYSIS":
            self._run_analysis()
            self.state = "AI_ANALYSIS"
        else:
            self.state = self.next_state_after_completion

    def _run_analysis(self):
        previous_strategy = self.ai.strategy
        player_type, new_strategy = self.ai.analyze_and_adapt(self.stats)
        self.analysis_player_type = player_type
        self.analysis_scores = self.ai.last_scores
        self.analysis_previous_strategy = previous_strategy
        self.analysis_new_strategy = new_strategy
        self.analysis_is_final = not self.ai.learning_enabled

    def _update_gameplay(self, dt):
        keys = pygame.key.get_pressed()

        moved = self.player.handle_input(keys, self.walls)
        self.stats.record_movement(moved)
        self.player.update_timers(dt)

        # continuous fire while holding SPACE or the mouse button
        if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]:
            self._player_shoot()

        # ---- enemies ----
        for enemy in self.enemies:
            enemy.strategy = self.ai.strategy  # applies live if strategy just changed
            bullet = enemy.update(dt, self.player, self.walls, self.grid)
            if bullet:
                self.bullets.append(bullet)

        # ---- bullets ----
        for bullet in self.bullets:
            bullet.update(self.walls)
        self._handle_bullet_collisions()
        self.bullets = [b for b in self.bullets if b.alive]

        # remove dead enemies
        self.enemies = [e for e in self.enemies if e.alive]

        # ---- per-frame behavior tracking ----
        nearest = None
        for enemy in self.enemies:
            d = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
            if nearest is None or d < nearest:
                nearest = d
        self.stats.record_frame(nearest)

        # ---- level end conditions ----
        if self.player.health <= 0:
            self.state = "GAME_OVER"
            return

        if not self.enemies:
            if self.state == "FINAL_BATTLE":
                self.start_completion_banner("FINAL BATTLE COMPLETE", "FINAL_DASHBOARD")
            else:
                self.start_completion_banner(f"LEVEL {self.current_level} COMPLETE", "AI_ANALYSIS")

    def _handle_bullet_collisions(self):
        for bullet in self.bullets:
            if not bullet.alive:
                continue

            if bullet.owner == "player":
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < bullet.radius + enemy.radius:
                        bullet.alive = False
                        self.stats.record_hit()
                        killed = enemy.take_damage(bullet.damage)
                        if killed:
                            self.stats.record_kill()
                            self.total_kills += 1
                        break

            elif bullet.owner == "enemy":
                if math.hypot(bullet.x - self.player.x, bullet.y - self.player.y) < bullet.radius + self.player.radius:
                    bullet.alive = False
                    self.player.take_damage(bullet.damage)

    # -----------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------
    def _draw(self):
        self.screen.fill(COLOR_BG)

        if self.state == "MENU":
            self._draw_menu()
        elif self.state in ("GAMEPLAY", "FINAL_BATTLE", "LEVEL_COMPLETE"):
            self._draw_arena()
            self._draw_hud()
            if self.state == "LEVEL_COMPLETE":
                self._draw_banner(self.completion_message)
        elif self.state == "AI_ANALYSIS":
            self._draw_arena()
            self._draw_hud()
            self._draw_analysis_panel()
        elif self.state == "GAME_OVER":
            self._draw_arena()
            self._draw_hud()
            self._draw_banner("GAME OVER", sub="Press ENTER to return to the menu", color=COLOR_BAD)
        elif self.state == "FINAL_DASHBOARD":
            self._draw_dashboard()

    def _draw_arena(self):
        pygame.draw.rect(self.screen, COLOR_ARENA_BG,
                          (0, ARENA_TOP, SCREEN_WIDTH, ARENA_BOTTOM - ARENA_TOP))
        for wall in self.walls:
            pygame.draw.rect(self.screen, COLOR_WALL, wall)

        for enemy in self.enemies:
            enemy.draw(self.screen, self.font_small, self.debug_mode)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        self.player.draw(self.screen)

        if self.debug_mode:
            self._draw_debug_overlay()

    def _draw_debug_overlay(self):
        lines = [
            f"Strategy: {self.ai.strategy}   Learning: {self.ai.learning_enabled}",
            f"Enemies alive: {len(self.enemies)}   Bullets: {len(self.bullets)}",
        ]
        for i, line in enumerate(lines):
            surf = self.font_small.render(line, True, COLOR_WARN)
            self.screen.blit(surf, (10, ARENA_TOP + 8 + i * 18))

    def _draw_hud(self):
        pygame.draw.rect(self.screen, COLOR_UI_BG, (0, 0, SCREEN_WIDTH, UI_HEIGHT))

        level_label = "FINAL BATTLE" if self.state == "FINAL_BATTLE" else f"LEVEL {self.current_level}/{TOTAL_LEARNING_LEVELS}"
        learning_label = "LEARNING" if self.ai.learning_enabled else "LEARNING COMPLETE"
        learning_color = COLOR_ACCENT if self.ai.learning_enabled else COLOR_GOOD

        pieces = [
            (f"HP: {int(self.player.health)}", COLOR_GOOD if self.player.health > 30 else COLOR_BAD),
            (level_label, COLOR_TEXT),
            (f"ENEMIES: {len(self.enemies)}", COLOR_TEXT),
            (f"AI: {learning_label}", learning_color),
            (f"TYPE: {self.ai.last_player_type or '---'}", COLOR_TEXT_DIM),
            (f"STRATEGY: {self.ai.strategy}", COLOR_WARN),
        ]

        x = 16
        for text, color in pieces:
            surf = self.font_medium.render(text, True, color)
            self.screen.blit(surf, (x, UI_HEIGHT // 2 - surf.get_height() // 2))
            x += surf.get_width() + 26

    def _draw_menu(self):
        title = self.font_title.render("EVOARENA", True, COLOR_ACCENT)
        subtitle = self.font_medium.render("An Adaptive 2D Battle Arena", True, COLOR_TEXT)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 170))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 240))

        lines = [
            "WASD to move   |   SPACE or LEFT CLICK to shoot (aim with mouse)",
            "Enemies observe how you play across 3 levels, then adapt their strategy.",
            "",
            "Press ENTER to start",
            "(F1 toggles debug info, ESC quits)",
        ]
        y = 340
        for line in lines:
            surf = self.font_small.render(line, True, COLOR_TEXT_DIM)
            self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 28

    def _draw_banner(self, text, sub=None, color=COLOR_GOOD):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, UI_HEIGHT))

        surf = self.font_large.render(text, True, color)
        self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT // 2 - 40))

        if sub:
            sub_surf = self.font_small.render(sub, True, COLOR_TEXT_DIM)
            self.screen.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def _draw_analysis_panel(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, UI_HEIGHT))

        panel_w, panel_h = 560, 400
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2
        panel_y = UI_HEIGHT + 50
        pygame.draw.rect(self.screen, (28, 28, 40), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        header = "LEARNING COMPLETE" if self.analysis_is_final else "AI ANALYSIS"
        header_color = COLOR_GOOD if self.analysis_is_final else COLOR_ACCENT
        header_surf = self.font_large.render(header, True, header_color)
        self.screen.blit(header_surf, (SCREEN_WIDTH // 2 - header_surf.get_width() // 2, panel_y + 20))

        y = panel_y + 90
        label = "Final Player Type:" if self.analysis_is_final else "Player Type:"
        self._draw_kv(label, self.analysis_player_type or "-", panel_x + 30, y)
        y += 36

        for player_type in ("AGGRESSIVE", "DEFENSIVE", "RANGED"):
            pct = self.analysis_scores.get(player_type, 0)
            self._draw_kv(f"{player_type} Score:", f"{pct}%", panel_x + 30, y)
            y += 30

        y += 10
        if self.analysis_is_final:
            self._draw_kv("Final Enemy Strategy:", self.analysis_new_strategy, panel_x + 30, y)
            y += 36
            self._draw_kv("Adaptation Score:", f"{self.ai.adaptation_score}%", panel_x + 30, y)
            y += 36
            self._draw_kv("AI Learning:", "DISABLED", panel_x + 30, y, value_color=COLOR_BAD)
        else:
            self._draw_kv("Previous Strategy:", self.analysis_previous_strategy, panel_x + 30, y)
            y += 30
            self._draw_kv("New Strategy:", self.analysis_new_strategy, panel_x + 30, y)
            y += 36
            self._draw_kv("Learning Progress:", f"{self.ai.level_count} / {TOTAL_LEARNING_LEVELS}", panel_x + 30, y)

        prompt = "Press ENTER for the Final Battle" if self.analysis_is_final else "Press ENTER for the next level"
        prompt_surf = self.font_small.render(prompt, True, COLOR_TEXT_DIM)
        self.screen.blit(prompt_surf, (SCREEN_WIDTH // 2 - prompt_surf.get_width() // 2, panel_y + panel_h - 36))

    def _draw_kv(self, key, value, x, y, value_color=COLOR_TEXT):
        key_surf = self.font_medium.render(key, True, COLOR_TEXT_DIM)
        value_surf = self.font_medium.render(str(value), True, value_color)
        self.screen.blit(key_surf, (x, y))
        self.screen.blit(value_surf, (x + 260, y))

    def _draw_dashboard(self):
        header = self.font_title.render("EVOARENA AI PERFORMANCE REPORT", True, COLOR_ACCENT)
        self.screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 40))

        left_x = 80
        y = 130
        rows = [
            ("Player Type", self.ai.last_player_type or "-"),
            ("Final AI Strategy", self.ai.strategy),
            ("Levels Observed", str(TOTAL_LEARNING_LEVELS)),
            ("Bullets Fired (total)", str(self.total_bullets_fired)),
            ("Enemies Defeated (total)", str(self.total_kills)),
            ("Average Distance to Enemy", f"{int(self.stats.average_distance)} px"),
            ("Adaptation Score", f"{self.ai.adaptation_score}%"),
            ("Learning Status", "COMPLETE" if not self.ai.learning_enabled else "IN PROGRESS"),
        ]
        for key, value in rows:
            self._draw_kv(key + ":", value, left_x, y)
            y += 34

        # adaptation history text
        history_x = 80
        history_y = y + 20
        history_title = self.font_medium.render("Strategy Adaptation History:", True, COLOR_TEXT)
        self.screen.blit(history_title, (history_x, history_y))
        history_y += 32
        for level_num, strategy in self.ai.history:
            label = "Start" if level_num == 0 else f"Level {level_num}"
            line = self.font_small.render(f"{label}  ->  {strategy}", True, COLOR_TEXT_DIM)
            self.screen.blit(line, (history_x + 10, history_y))
            history_y += 24

        # simple bar chart of the three player-type scores, made of rectangles
        chart_x = 560
        chart_y = 130
        chart_w = 320
        bar_h = 34
        gap = 16
        max_pct = max(self.ai.last_scores.values()) if self.ai.last_scores else 1
        max_pct = max(max_pct, 1)

        chart_title = self.font_medium.render("Player Type Breakdown", True, COLOR_TEXT)
        self.screen.blit(chart_title, (chart_x, chart_y - 34))

        colors = {"AGGRESSIVE": COLOR_BAD, "DEFENSIVE": COLOR_ACCENT, "RANGED": COLOR_WARN}
        for i, player_type in enumerate(("AGGRESSIVE", "DEFENSIVE", "RANGED")):
            pct = self.ai.last_scores.get(player_type, 0)
            bar_width = int((pct / max_pct) * chart_w)
            bar_y = chart_y + i * (bar_h + gap)
            pygame.draw.rect(self.screen, (50, 50, 62), (chart_x, bar_y, chart_w, bar_h))
            pygame.draw.rect(self.screen, colors[player_type], (chart_x, bar_y, bar_width, bar_h))
            label = self.font_small.render(f"{player_type} {pct}%", True, COLOR_TEXT)
            self.screen.blit(label, (chart_x + 8, bar_y + bar_h // 2 - 8))

        prompt = self.font_small.render("Press ENTER to return to the menu", True, COLOR_TEXT_DIM)
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, SCREEN_HEIGHT - 40))
