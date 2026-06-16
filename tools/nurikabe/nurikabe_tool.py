from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    grid = input_data.get("grid")
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty array of strings.")

    height = len(grid)
    width = None
    clues: List[Dict[str, Any]] = []
    for row_index, row in enumerate(grid):
        if isinstance(row, list):
            row = "".join(str(cell).strip() for cell in row)
        if not isinstance(row, str):
            raise ValueError(f"Grid row {row_index + 1} must be a string.")
        row = "".join(row.split())
        if width is None:
            width = len(row)
        if len(row) != width:
            raise ValueError("All grid rows must have the same length.")
        for col_index, char in enumerate(row):
            if char == ".":
                continue
            if not char.isdigit() or char == "0":
                raise ValueError(f"Invalid clue at row {row_index + 1}, column {col_index + 1}: expected a positive digit or '.'.")
            clues.append({"row": row_index, "col": col_index, "value": int(char)})

    if width is None:
        raise ValueError("grid must contain at least one row.")

    solution = _solve_nurikabe(height, width, clues)
    if solution is None:
        raise ValueError("Unable to solve the provided Nurikabe puzzle. Verify the numbered islands and the grid shape.")

    return {"solution": ["".join("1" if cell else "0" for cell in row) for row in solution]}


def _solve_nurikabe(height: int, width: int, clues: List[Dict[str, Any]]) -> Optional[List[List[bool]]]:
    assignment: List[List[Optional[int]]] = [[None] * width for _ in range(height)]
    for ridx, clue in enumerate(clues):
        assignment[clue["row"]][clue["col"]] = ridx

    clues_sorted = sorted(clues, key=lambda clue: clue["value"])

    def search(clue_index: int, assigned: List[List[Optional[int]]]) -> Optional[List[List[bool]]]:
        if clue_index == len(clues_sorted):
            return _finalize_nurikabe(assigned, height, width)

        clue = clues_sorted[clue_index]
        clue_id = clue_index
        size = clue["value"]
        base_id = assigned[clue["row"]][clue["col"]]
        if base_id is None:
            return None

        for shape in _generate_island_shapes(clue["row"], clue["col"], size, assigned):
            new_assign = [list(row) for row in assigned]
            for r, c in shape:
                new_assign[r][c] = clue_id
            if _island_adjacent_to_another(new_assign, height, width):
                continue
            result = search(clue_index + 1, new_assign)
            if result is not None:
                return result
        return None

    return search(0, assignment)


def _generate_island_shapes(start_row: int, start_col: int, size: int, assigned: List[List[Optional[int]]]) -> List[List[Tuple[int, int]]]:
    if size == 1:
        return [[(start_row, start_col)]]

    shapes: List[List[Tuple[int, int]]] = []
    visited_shapes: Set[Tuple[Tuple[int, int], ...]] = set()

    def expand(shape: List[Tuple[int, int]], frontier: Set[Tuple[int, int]]) -> None:
        if len(shape) == size:
            key = tuple(sorted(shape))
            if key not in visited_shapes:
                visited_shapes.add(key)
                shapes.append(shape[:])
            return

        for cell in sorted(frontier):
            r, c = cell
            if assigned[r][c] is not None and assigned[r][c] != assigned[start_row][start_col]:
                continue
            if _touches_other_island(cell, shape, assigned):
                continue
            new_shape = shape + [cell]
            new_frontier = set(frontier)
            new_frontier.remove(cell)
            for nr, nc in _neighbors(r, c, len(assigned), len(assigned[0])):
                if (nr, nc) not in new_shape and assigned[nr][nc] is None:
                    new_frontier.add((nr, nc))
            expand(new_shape, new_frontier)

    initial = [(start_row, start_col)]
    frontier = set()
    for neighbor in _neighbors(start_row, start_col, len(assigned), len(assigned[0])):
        if assigned[neighbor[0]][neighbor[1]] is None:
            frontier.add(neighbor)
    expand(initial, frontier)
    return shapes


def _neighbors(row: int, col: int, height: int, width: int) -> List[Tuple[int, int]]:
    candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
    return [(r, c) for r, c in candidates if 0 <= r < height and 0 <= c < width]


def _touches_other_island(cell: Tuple[int, int], shape: List[Tuple[int, int]], assigned: List[List[Optional[int]]]) -> bool:
    r, c = cell
    for nr, nc in _neighbors(r, c, len(assigned), len(assigned[0])):
        if (nr, nc) in shape:
            continue
        if assigned[nr][nc] is not None and assigned[nr][nc] != assigned[r][c]:
            return True
    return False


def _island_adjacent_to_another(assigned: List[List[Optional[int]]], height: int, width: int) -> bool:
    for r in range(height):
        for c in range(width):
            value = assigned[r][c]
            if value is None:
                continue
            for nr, nc in _neighbors(r, c, height, width):
                neighbor = assigned[nr][nc]
                if neighbor is None or neighbor == value:
                    continue
                return True
    return False


def _finalize_nurikabe(assigned: List[List[Optional[int]]], height: int, width: int) -> Optional[List[List[bool]]]:
    result: List[List[bool]] = [[False] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            if assigned[r][c] is None:
                result[r][c] = False
            else:
                result[r][c] = True

    if not _sea_is_connected(result, height, width):
        return None
    if _contains_2x2_water(result, height, width):
        return None
    return result


def _sea_is_connected(island_map: List[List[bool]], height: int, width: int) -> bool:
    water_cells = [(r, c) for r in range(height) for c in range(width) if not island_map[r][c]]
    if not water_cells:
        return True

    queue = deque([water_cells[0]])
    visited: Set[Tuple[int, int]] = {water_cells[0]}
    while queue:
        r, c = queue.popleft()
        for nr, nc in _neighbors(r, c, height, width):
            if not island_map[nr][nc] and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))

    return len(visited) == len(water_cells)


def _contains_2x2_water(island_map: List[List[bool]], height: int, width: int) -> bool:
    for r in range(height - 1):
        for c in range(width - 1):
            if not island_map[r][c] and not island_map[r][c + 1] and not island_map[r + 1][c] and not island_map[r + 1][c + 1]:
                return True
    return False
