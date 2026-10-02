"""
settings.py
-----------
All shared constants live here so every other file can import them
without creating circular imports (game.py, player.py, enemy.py, etc.
all need the same numbers, but they also import each other).

Nothing in this file "does" anything - it is just numbers and colors.
"""

# ---------------------------------------------------------------
# SCREEN / ARENA LAYOUT
# ---------------------------------------------------------------
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
UI_HEIGHT = 60          # top strip reserved for the HUD text
FPS = 60

# The arena is the playable rectangle BELOW the HUD strip.
ARENA_TOP = UI_HEIGHT
ARENA_LEFT = 0
ARENA_RIGHT = SCREEN_WIDTH
ARENA_BOTTOM = SCREEN_HEIGHT

# ---------------------------------------------------------------
# COLORS  (dark, clean, "modern" look using flat shapes only)
# ---------------------------------------------------------------
COLOR_BG = (18, 18, 26)
COLOR_ARENA_BG = (26, 26, 36)
COLOR_UI_BG = (12, 12, 18)
COLOR_WALL = (95, 95, 110)
COLOR_TEXT = (230, 230, 235)
COLOR_TEXT_DIM = (150, 150, 160)
COLOR_ACCENT = (90, 200, 255)
COLOR_GOOD = (110, 220, 130)
COLOR_BAD = (230, 90, 90)
COLOR_WARN = (240, 190, 90)

COLOR_PLAYER = (60, 140, 255)
COLOR_PLAYER_BULLET = (255, 240, 140)

COLOR_CHASER = (220, 60, 60)
COLOR_SHOOTER = (170, 70, 220)
COLOR_FLANKER = (235, 150, 40)
COLOR_ENEMY_BULLET = (255, 120, 120)

# ---------------------------------------------------------------
# PLAYER
# ---------------------------------------------------------------
PLAYER_RADIUS = 14
PLAYER_SPEED = 4.5
PLAYER_MAX_HEALTH = 100
PLAYER_SHOOT_COOLDOWN = 0.22        # seconds between shots
PLAYER_BULLET_SPEED = 11
PLAYER_BULLET_DAMAGE = 12
PLAYER_BULLET_RADIUS = 5

# ---------------------------------------------------------------
# ENEMY (base values, tweaked slightly per role in enemy.py)
# ---------------------------------------------------------------
ENEMY_RADIUS = 13
ENEMY_MAX_HEALTH = 45
ENEMY_LOW_HEALTH_RATIO = 0.30        # below this fraction -> RETREAT
ENEMY_DETECTION_RADIUS = 260         # PATROL -> CHASE
ENEMY_CONTACT_DAMAGE = 10            # melee hit damage (chaser/flanker)
ENEMY_CONTACT_COOLDOWN = 0.6         # seconds between melee hits
ENEMY_BULLET_SPEED = 7
ENEMY_BULLET_DAMAGE = 8
ENEMY_BULLET_RADIUS = 5
ENEMY_SHOOT_COOLDOWN = 1.4

ROLES = ["chaser", "shooter", "flanker"]

# Attack range = distance at which state becomes ATTACK, per role
ATTACK_RADIUS = {
    "chaser": 40,
    "shooter": 230,
    "flanker": 55,
}

# Base movement speed per role
ENEMY_SPEED = {
    "chaser": 2.6,
    "shooter": 2.0,
    "flanker": 2.8,
}

# ---------------------------------------------------------------
# A* / GRID PATHFINDING
# ---------------------------------------------------------------
CELL_SIZE = 20
GRID_COLS = SCREEN_WIDTH // CELL_SIZE
GRID_ROWS = (SCREEN_HEIGHT - UI_HEIGHT) // CELL_SIZE
PATH_RECALC_FRAMES = 20   # recompute A* path this often (not every frame)

# ---------------------------------------------------------------
# PLAYER BEHAVIOR ANALYSIS
# ---------------------------------------------------------------
NEAR_THRESHOLD = 110      # px: closer than this counts as "near an enemy"
FAR_THRESHOLD = 260       # px: farther than this counts as "far from enemies"

PLAYER_TYPES = ["AGGRESSIVE", "DEFENSIVE", "RANGED"]
STRATEGIES = ["RUSH", "SURROUND", "KEEP_DISTANCE"]

# Rule-based mapping: detected player type -> enemy strategy
STRATEGY_MAP = {
    "AGGRESSIVE": "SURROUND",
    "DEFENSIVE": "RUSH",
    "RANGED": "KEEP_DISTANCE",
}

SURROUND_RADIUS = 130          # ring distance used by SURROUND strategy
KEEP_DISTANCE_RING = 220       # preferred distance used by KEEP_DISTANCE strategy

# ---------------------------------------------------------------
# LEVELS
# ---------------------------------------------------------------
TOTAL_LEARNING_LEVELS = 3

# (num_chasers, num_shooters, num_flankers) per level
LEVEL_ENEMY_COUNTS = {
    1: (1, 1, 1),
    2: (1, 2, 1),
    3: (2, 2, 1),
}
FINAL_BATTLE_ENEMY_COUNT = (2, 2, 2)

# ---------------------------------------------------------------
# DEBUG
# ---------------------------------------------------------------
DEBUG_MODE = False
