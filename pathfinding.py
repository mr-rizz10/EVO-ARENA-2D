"""
pathfinding.py
--------------
A small, beginner-friendly A* implementation on a grid.

The arena is divided into square cells (CELL_SIZE x CELL_SIZE).
A cell is either:
    0 = walkable
    1 = obstacle (wall)

Enemies convert their (x, y) pixel position into a grid cell,
ask this module for a path to the player's grid cell, and then
follow that path pixel-by-pixel in enemy.py.

This is intentionally simple: 4-directional movement (no diagonals)
and a Manhattan-distance heuristic. That is enough to route around
the rectangular walls in this project.
"""

import heapq
from settings import CELL_SIZE, GRID_COLS, GRID_ROWS, UI_HEIGHT


def build_grid(walls):
    """
    Turns the list of wall rectangles (pygame.Rect) into a 2D grid
    of 0s (walkable) and 1s (blocked).

    grid[row][col]  -> 0 or 1
    """
    grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_center_x = col * CELL_SIZE + CELL_SIZE // 2
            cell_center_y = UI_HEIGHT + row * CELL_SIZE + CELL_SIZE // 2

            for wall in walls:
                if wall.collidepoint(cell_center_x, cell_center_y):
                    grid[row][col] = 1
                    break

    return grid


def world_to_grid(x, y):
    """Convert a pixel position into a (col, row) grid coordinate."""
    col = int(x // CELL_SIZE)
    row = int((y - UI_HEIGHT) // CELL_SIZE)
    col = max(0, min(GRID_COLS - 1, col))
    row = max(0, min(GRID_ROWS - 1, row))
    return col, row


def grid_to_world(col, row):
    """Convert a (col, row) grid coordinate into the pixel center of that cell."""
    x = col * CELL_SIZE + CELL_SIZE // 2
    y = UI_HEIGHT + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def _neighbors(grid, col, row):
    """Return walkable neighbor cells (up, down, left, right)."""
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    candidates = [(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)]
    result = []
    for c, r in candidates:
        if 0 <= r < rows and 0 <= c < cols:
            if grid[r][c] == 0:
                result.append((c, r))
    return result


def _heuristic(a, b):
    """Manhattan distance - fast and good enough for a 4-direction grid."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal, max_iterations=2500):
    """
    Classic A* search on the grid.

    start, goal : (col, row) tuples
    Returns a list of (col, row) cells from just after `start` up to
    and including `goal`. Returns an empty list if no path is found
    (or start == goal, or the goal cell is itself a wall).
    """
    if start == goal:
        return []

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    goal_is_wall = True
    if 0 <= goal[1] < rows and 0 <= goal[0] < cols:
        goal_is_wall = grid[goal[1]][goal[0]] == 1
    if goal_is_wall:
        return []

    open_heap = []
    heapq.heappush(open_heap, (0, start))

    came_from = {}
    g_score = {start: 0}

    iterations = 0

    while open_heap:
        iterations += 1
        if iterations > max_iterations:
            return []  # safety valve - avoid ever freezing the game

        _, current = heapq.heappop(open_heap)

        if current == goal:
            return _reconstruct_path(came_from, current)

        for neighbor in _neighbors(grid, current[0], current[1]):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score = tentative_g + _heuristic(neighbor, goal)
                came_from[neighbor] = current
                heapq.heappush(open_heap, (f_score, neighbor))

    return []  # no path exists (fully boxed in by walls)


def _reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path[1:]  # drop the starting cell, keep the rest
