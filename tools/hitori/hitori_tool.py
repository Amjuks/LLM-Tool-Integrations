from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    grid = input_data.get("grid")
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be an array of rows containing digits.")

    parsed: List[List[int]] = []
    width = None
    for row_index, row in enumerate(grid):
        if not isinstance(row, str):
            raise ValueError(f"Grid row {row_index + 1} must be a string.")
        row = row.strip()
        if width is None:
            width = len(row)
        if len(row) != width:
            raise ValueError("All grid rows must have the same length.")
        if not row or any(not ch.isdigit() or ch == "0" for ch in row):
            raise ValueError(f"Invalid Hitori row {row_index + 1}: rows must contain digits 1-9 only.")
        parsed.append([int(ch) for ch in row])

    if width is None:
        raise ValueError("grid must contain at least one row.")

    solution = _solve_hitori(parsed)
    if solution is None:
        raise ValueError("Unable to solve the provided Hitori puzzle. The input may be inconsistent or too ambiguous.")

    return {"solution": ["".join("B" if cell else "W" for cell in row) for row in solution]}


def _solve_hitori(grid: List[List[int]]) -> Optional[List[List[bool]]]:
    n = len(grid)
    solution: List[List[Optional[bool]]] = [[None] * n for _ in range(n)]

    def is_valid_assignment(r: int, c: int, black: bool) -> bool:
        if black:
            for nr, nc in _neighbors(r, c, n, n):
                if solution[nr][nc] is True:
                    return False
            return True

        value = grid[r][c]
        for nc in range(n):
            if nc != c and solution[r][nc] is False and grid[r][nc] == value:
                return False
        for nr in range(n):
            if nr != r and solution[nr][c] is False and grid[nr][c] == value:
                return False
        return True

    def backtrack(index: int) -> bool:
        if index == n * n:
            return _all_white_connected(solution, grid)

        r, c = divmod(index, n)
        for black in (False, True):
            if not is_valid_assignment(r, c, black):
                continue
            solution[r][c] = black
            if backtrack(index + 1):
                return True
            solution[r][c] = None
        return False

    if backtrack(0):
        return [[bool(cell) for cell in row] for row in solution]  # True means black
    return None


def _neighbors(row: int, col: int, height: int, width: int) -> List[Tuple[int, int]]:
    candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
    return [(r, c) for r, c in candidates if 0 <= r < height and 0 <= c < width]


def _all_white_connected(solution: List[List[Optional[bool]]], grid: List[List[int]]) -> bool:
    n = len(grid)
    white_cells = [(r, c) for r in range(n) for c in range(n) if solution[r][c] is False]
    if not white_cells:
        return False

    queue = deque([white_cells[0]])
    visited: Set[Tuple[int, int]] = {white_cells[0]}
    while queue:
        r, c = queue.popleft()
        for nr, nc in _neighbors(r, c, n, n):
            if (nr, nc) not in visited and solution[nr][nc] is False:
                visited.add((nr, nc))
                queue.append((nr, nc))

    return len(visited) == len(white_cells)
