from itertools import combinations
from typing import Any, Dict, List, Optional, Set, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    regions = input_data.get("regions")
    stars_per_region = input_data.get("stars_per_region", 2)

    if not isinstance(regions, list) or not regions:
        raise ValueError("regions must be a non-empty array of string rows.")
    if not isinstance(stars_per_region, int) or stars_per_region < 1:
        raise ValueError("stars_per_region must be a positive integer.")

    grid: List[List[str]] = []
    width = None
    for row_index, row in enumerate(regions):
        if not isinstance(row, list) or not row:
            raise ValueError(f"Region row {row_index + 1} must be an array of region labels.")
        if width is None:
            width = len(row)
        if len(row) != width:
            raise ValueError("All region rows must have the same length.")
        for col_index, label in enumerate(row):
            if not isinstance(label, str) or not label:
                raise ValueError(f"Region label at row {row_index + 1}, column {col_index + 1} must be a non-empty string.")
        grid.append(row)

    if width is None:
        raise ValueError("regions must contain at least one row.")

    solution = _solve_star_battle(grid, stars_per_region)
    if solution is None:
        raise ValueError("Unable to solve the provided Star Battle puzzle. Check region labels and the requested stars per region.")

    output = ["".join("*" if cell else "." for cell in row) for row in solution]
    return {"solution": output}


def _solve_star_battle(grid: List[List[str]], stars_per_region: int) -> Optional[List[List[bool]]]:
    rows = len(grid)
    cols = len(grid[0])
    region_cells: Dict[str, List[Tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, label in enumerate(row):
            region_cells.setdefault(label, []).append((r, c))

    expected_region_count = stars_per_region
    region_ids = list(region_cells.keys())
    row_solution: List[List[bool]] = [[False] * cols for _ in range(rows)]
    col_counts = [0] * cols
    region_counts = {region: 0 for region in region_ids}

    def can_place(r: int, c: int) -> bool:
        if any(row_solution[x][c] for x in range(rows)):
            return False
        if any(row_solution[r][x] for x in range(cols)):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and row_solution[nr][nc]:
                    return False
        return True

    def backtrack(row: int) -> bool:
        if row == rows:
            return all(count == expected_region_count for count in region_counts.values())

        available_cols = [c for c in range(cols) if can_place(row, c)]
        for selection in combinations(range(cols), expected_region_count):
            if any(c not in available_cols for c in selection):
                continue
            selected_regions: Dict[str, int] = {}
            valid = True
            for c in selection:
                label = grid[row][c]
                selected_regions[label] = selected_regions.get(label, 0) + 1
                if region_counts[label] + selected_regions[label] > expected_region_count:
                    valid = False
                    break
            if not valid:
                continue
            for c in selection:
                row_solution[row][c] = True
                col_counts[c] += 1
                region_counts[grid[row][c]] += 1
            if backtrack(row + 1):
                return True
            for c in selection:
                row_solution[row][c] = False
                col_counts[c] -= 1
                region_counts[grid[row][c]] -= 1
        return False

    if backtrack(0):
        return row_solution
    return None
