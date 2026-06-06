from typing import Any, Dict, List, Optional, Set, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    cells = input_data.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("cells must be a non-empty array of rows.")

    parsed: List[List[str]] = []
    width = None
    for row_index, row in enumerate(cells):
        if not isinstance(row, list) or not row:
            raise ValueError(f"Kakuro row {row_index + 1} must be an array of cell definitions.")
        if width is None:
            width = len(row)
        if len(row) != width:
            raise ValueError("All Kakuro rows must have the same length.")
        parsed_row: List[str] = []
        for col_index, cell in enumerate(row):
            if not isinstance(cell, str) or not cell:
                raise ValueError(f"Invalid Kakuro cell at row {row_index + 1}, column {col_index + 1}.")
            parsed_row.append(cell.strip().lower())
        parsed.append(parsed_row)

    solution = _solve_kakuro(parsed)
    if solution is None:
        raise ValueError("Unable to solve the provided Kakuro puzzle. Check the grid layout and clue sums.")

    return {"solution": ["".join(value for value in row) for row in solution]}


def _solve_kakuro(cells: List[List[str]]) -> Optional[List[List[str]]]:
    height = len(cells)
    width = len(cells[0])

    white_cells: List[Tuple[int, int]] = []
    clue_cells: Dict[Tuple[int, int], Dict[str, int]] = {}
    for r in range(height):
        for c in range(width):
            cell = cells[r][c]
            if cell in {"x", "black", "#"}:
                continue
            if cell == ".":
                white_cells.append((r, c))
                continue
            clue_cells[(r, c)] = _parse_clue(cell, r, c)

    across = _build_segments(cells, clue_cells, width, height, direction="across")
    down = _build_segments(cells, clue_cells, width, height, direction="down")
    if not across and not down:
        raise ValueError("Kakuro grid must contain at least one clue segment.")

    solution: List[List[Optional[int]]] = [[None] * width for _ in range(height)]

    def backtrack(index: int) -> bool:
        if index == len(white_cells):
            return True
        r, c = white_cells[index]
        for candidate in range(1, 10):
            solution[r][c] = candidate
            if _is_valid_kakuro_cell(solution, across, down, r, c):
                if backtrack(index + 1):
                    return True
        solution[r][c] = None
        return False

    if not backtrack(0):
        return None

    return [[str(cell) if cell is not None else "." for cell in row] for row in solution]


def _parse_clue(cell: str, row: int, col: int) -> Dict[str, int]:
    clue: Dict[str, int] = {}
    if cell in {"x", "black", "#"}:
        return clue
    if cell.startswith("r") or "c" in cell:
        parts = cell.replace(" ", "").split("c")
        if parts[0].startswith("r") and parts[0] != "r":
            clue["across"] = int(parts[0][1:])
        if len(parts) == 2 and parts[1]:
            clue["down"] = int(parts[1])
        return clue
    raise ValueError(f"Invalid Kakuro clue format at cell '{cell}' on row {row + 1}, column {col + 1}.")


def _build_segments(cells: List[List[str]], clue_cells: Dict[Tuple[int, int], Dict[str, int]], width: int, height: int, direction: str) -> List[Dict[str, Any]]:
    segments: List[Dict[str, Any]] = []
    for (r, c), clue in clue_cells.items():
        key = "across" if direction == "across" else "down"
        if key not in clue:
            continue
        positions: List[Tuple[int, int]] = []
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        rr, cc = r + dr, c + dc
        while 0 <= rr < height and 0 <= cc < width and cells[rr][cc] == ".":
            positions.append((rr, cc))
            rr += dr
            cc += dc
        if not positions:
            raise ValueError(f"Kakuro clue at row {r + 1}, column {c + 1} has no white cells in the {direction} direction.")
        segments.append({"cells": positions, "target": clue[key], "direction": direction})
    return segments


def _is_valid_kakuro_cell(solution: List[List[Optional[int]]], across: List[Dict[str, Any]], down: List[Dict[str, Any]], row: int, col: int) -> bool:
    for segment in across + down:
        if (row, col) not in segment["cells"]:
            continue
        values = [solution[r][c] for r, c in segment["cells"]]
        if any(val is not None and (val < 1 or val > 9) for val in values):
            return False
        seen: Set[int] = set()
        total = 0
        filled = True
        for val in values:
            if val is None:
                filled = False
                continue
            if val in seen:
                return False
            seen.add(val)
            total += val
        if filled and total != segment["target"]:
            return False
        if not filled and total >= segment["target"]:
            return False
    return True
