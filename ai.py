"""
brain of evoarena
"""

from settings import (
    NEAR_THRESHOLD, FAR_THRESHOLD, STRATEGY_MAP,
    TOTAL_LEARNING_LEVELS, PLAYER_TYPES,
)


class PlayerStats:
    """Raw gameplay statistics collected during a single level."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.distance_moved = 0.0
        self.bullets_fired = 0
        self.hits_landed = 0
        self.enemies_killed = 0

        self._distance_sum = 0.0
        self._distance_samples = 0

        self.time_near_frames = 0     # frames spent close to an enemy
        self.time_far_frames = 0      # frames spent far from every enemy
        self.total_frames = 0

    # --- recording methods, called every frame / event from game.py ---
    def record_movement(self, distance):
        self.distance_moved += distance

    def record_shot(self):
        self.bullets_fired += 1

    def record_hit(self):
        self.hits_landed += 1

    def record_kill(self):
        self.enemies_killed += 1

    def record_frame(self, nearest_enemy_distance):
        """Call once per frame with the distance to the CLOSEST living enemy."""
        self.total_frames += 1
        if nearest_enemy_distance is None:
            return
        self._distance_sum += nearest_enemy_distance
        self._distance_samples += 1
        if nearest_enemy_distance < NEAR_THRESHOLD:
            self.time_near_frames += 1
        elif nearest_enemy_distance > FAR_THRESHOLD:
            self.time_far_frames += 1

    @property
    def average_distance(self):
        if self._distance_samples == 0:
            return 0.0
        return self._distance_sum / self._distance_samples

    @property
    def near_ratio(self):
        if self.total_frames == 0:
            return 0.0
        return self.time_near_frames / self.total_frames

    @property
    def far_ratio(self):
        if self.total_frames == 0:
            return 0.0
        return self.time_far_frames / self.total_frames

    @property
    def accuracy(self):
        if self.bullets_fired == 0:
            return 0.0
        return self.hits_landed / self.bullets_fired


def classify_player(stats):
    """
    Rule-based classification (NOT machine learning).

    Every number below is a simple, hand-picked weight. They are
    grouped here on purpose so they are easy to find and tune during
    development or during the viva.

    Returns: (player_type_string, scores_dict)
        scores_dict maps each of PLAYER_TYPES to a 0-100 percentage.
    """
    near_ratio = stats.near_ratio
    far_ratio = stats.far_ratio

    # --- raw (un-normalized) scores -----------------------------
    aggressive_raw = (
        near_ratio * 6.0
        + min(stats.distance_moved / 3000.0, 3.0)
        + stats.accuracy * 2.0
    )

    defensive_raw = (
        (1.0 - near_ratio - far_ratio) * 5.0
        + max(0.0, 3.0 - stats.distance_moved / 2000.0)
        + max(0.0, 2.0 - stats.bullets_fired / 15.0)
    )

    ranged_raw = (
        far_ratio * 6.0
        + min(stats.bullets_fired / 25.0, 3.0)
        + min(stats.average_distance / 300.0, 2.0)
    )

    raw_scores = {
        "AGGRESSIVE": max(0.0, aggressive_raw),
        "DEFENSIVE": max(0.0, defensive_raw),
        "RANGED": max(0.0, ranged_raw),
    }

    total = sum(raw_scores.values())
    if total <= 0:
        # No meaningful data yet (e.g. level ended instantly) - default evenly.
        percentages = {t: round(100 / len(PLAYER_TYPES)) for t in PLAYER_TYPES}
    else:
        percentages = {t: round(raw_scores[t] / total * 100) for t in PLAYER_TYPES}

    player_type = max(percentages, key=percentages.get)
    return player_type, percentages


def compute_adaptation_score(confidence_percent, strategy_changed, level_count):
    """
    A simple, clearly-labeled PROJECT METRIC (not a scientific measure).

    It rewards:
      - how confidently the player was classified (their top score %)
      - whether the AI actually changed its strategy in response
      - how many of the 3 learning levels have been completed so far
    """
    score = confidence_percent * 0.6
    score += 25 if strategy_changed else 10
    score += level_count * (15 / TOTAL_LEARNING_LEVELS)
    return max(0, min(100, round(score)))


class AIController:
    """Owns the current enemy strategy and the bounded learning process."""

    def __init__(self):
        self.strategy = "RUSH"          # enemies' starting behavior on Level 1
        self.learning_enabled = True
        self.level_count = 0
        self.history = []                # list of (level_number, strategy_used)
        self.last_player_type = None
        self.last_scores = {t: 0 for t in PLAYER_TYPES}
        self.adaptation_score = 0

        self.history.append((0, self.strategy))  # strategy used during Level 1

    def analyze_and_adapt(self, stats):
        """
        Called at the END of a level. Analyzes the collected stats and,
        if learning is still enabled, updates self.strategy for the
        NEXT level. Returns (player_type, new_strategy).
        """
        player_type, scores = classify_player(stats)
        self.last_player_type = player_type
        self.last_scores = scores

        if self.learning_enabled:
            previous_strategy = self.strategy
            new_strategy = STRATEGY_MAP[player_type]
            strategy_changed = new_strategy != previous_strategy

            self.strategy = new_strategy
            self.level_count += 1
            self.history.append((self.level_count, self.strategy))

            self.adaptation_score = compute_adaptation_score(
                scores[player_type], strategy_changed, self.level_count
            )

            if self.level_count >= TOTAL_LEARNING_LEVELS:
                self.learning_enabled = False

        return player_type, self.strategy
