from typing import Any, Dict, List, Optional, Set, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    size = input_data.get("size")
    cages = input_data.get("cages")

    if not isinstance(size, int) or size < 3:
        raise ValueError("size must be an integer of at least 3.")
    if not isinstance(cages, list) or not cages:
        raise ValueError("cages must be a non-empty array of cage definitions.")

    parsed_cages = []
    cell_set = set()
    for index, cage in enumerate(cages, start=1):
        if not isinstance(cage, dict):
            raise ValueError(f"Cage {index} must be an object.")
        cells = cage.get("cells")
        target = cage.get("target")
        operation = cage.get("operation")
        if not isinstance(cells, list) or not cells:
            raise ValueError(f"Cage {index}: cells must be a non-empty array.")
        if not isinstance(target, int) or target < 1:
            raise ValueError(f"Cage {index}: target must be a positive integer.")
        if not isinstance(operation, str) or operation not in {"add", "mul", "sub", "div", "none"}:
            raise ValueError(f"Cage {index}: operation must be one of add, mul, sub, div, none.")

        coords: List[Tuple[int, int]] = []
        for cell in cells:
            if not isinstance(cell, dict):
                raise ValueError(f"Cage {index}: each cell must be an object with row and col.")
            row = cell.get("row")
            col = cell.get("col")
            if not isinstance(row, int) or not isinstance(col, int):
                raise ValueError(f"Cage {index}: cell coordinates must be integers.")
            if row < 0 or row >= size or col < 0 or col >= size:
                raise ValueError(f"Cage {index}: cell ({row}, {col}) is out of bounds for size {size}.")
            if (row, col) in cell_set:
                raise ValueError(f"Cage {index}: cell ({row}, {col}) appears in more than one cage.")
            cell_set.add((row, col))
            coords.append((row, col))

        if operation in {"sub", "div"} and len(coords) != 2:
            raise ValueError(f"Cage {index}: operation '{operation}' must have exactly 2 cells.")
        if operation == "none" and len(coords) != 1:
            raise ValueError(f"Cage {index}: operation 'none' must have exactly 1 cell.")

        parsed_cages.append({"cells": coords, "target": target, "operation": operation})

    if len(cell_set) != size * size:
        raise ValueError("Cages must cover every cell exactly once.")

    solution = _solve_kenken(size, parsed_cages)
    if solution is None:
        raise ValueError("Unable to solve the provided KenKen puzzle. Verify cage definitions and target operations.")

    return {"solution": ["".join(str(value) for value in row) for row in solution]}


def _solve_kenken(size: int, cages: List[Dict[str, Any]]) -> Optional[List[List[int]]]:
    grid: List[List[Optional[int]]] = [[None] * size for _ in range(size)]
    rows_used: List[Set[int]] = [set() for _ in range(size)]
    cols_used: List[Set[int]] = [set() for _ in range(size)]
    cage_map = {(r, c): cage for cage in cages for (r, c) in cage["cells"]}

    cells = [(r, c) for r in range(size) for c in range(size)]

    def evaluate_cage(cage: Dict[str, Any], values: List[int]) -> bool:
        operation = cage["operation"]
        target = cage["target"]
        if operation == "none":
            return values[0] == target
        if operation == "add":
            return sum(values) == target
        if operation == "mul":
            product = 1
            for value in values:
                product *= value
            return product == target
        if operation == "sub":
            a, b = values
            return abs(a - b) == target
        if operation == "div":
            a, b = values
            return (a / b == target) or (b / a == target)
        return False

    def cage_possible(cage: Dict[str, Any], values: List[Optional[int]]) -> bool:
        filled_values = [v for v in values if v is not None]
        if not filled_values:
            return True
        operation = cage["operation"]
        target = cage["target"]
        if operation == "none":
            return len(filled_values) <= 1 and (filled_values[0] == target if filled_values else True)
        if operation == "add":
            return sum(filled_values) <= target
        if operation == "mul":
            product = 1
            for v in filled_values:
                product *= v
            return product <= target
        if operation == "sub" or operation == "div":
            if len(filled_values) < 2:
                return True
            return evaluate_cage(cage, filled_values)
        return False

    def backtrack(index: int) -> bool:
        if index == size * size:
            return True
        r, c = cells[index]
        for candidate in range(1, size + 1):
            if candidate in rows_used[r] or candidate in cols_used[c]:
                continue
            grid[r][c] = candidate
            rows_used[r].add(candidate)
            cols_used[c].add(candidate)
            cage = cage_map[(r, c)]
            cage_values = [grid[cr][cc] for cr, cc in cage["cells"]]
            if cage_possible(cage, cage_values):
                if backtrack(index + 1):
                    return True
            rows_used[r].remove(candidate)
            cols_used[c].remove(candidate)
            grid[r][c] = None
        return False

    if backtrack(0):
        return [[grid[r][c] for c in range(size)] for r in range(size)]
    return None
