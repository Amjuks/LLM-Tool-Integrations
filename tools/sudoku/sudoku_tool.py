import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:

    puzzle = input_data.get("puzzle")
    if isinstance(puzzle, list) and len(puzzle) == 9:
        if all(isinstance(row, list) for row in puzzle):
            puzzle_rows = []
            for row_index, row in enumerate(puzzle):
                if not isinstance(row, list):
                    raise ValueError(f"Puzzle row {row_index+1} must be a list of 9 cell values.")
                if len(row) != 9:
                    raise ValueError(f"Puzzle row {row_index+1} must contain exactly 9 cells, got {len(row)}.")
                row_chars: List[str] = []
                for col_index, cell in enumerate(row):
                    if not isinstance(cell, str) or len(cell) != 1:
                        raise ValueError(
                            f"Puzzle cell at row {row_index+1}, column {col_index+1} must be a single character string."
                        )
                    normalized_cell = cell if cell != "0" else "."
                    if normalized_cell == ".":
                        row_chars.append(normalized_cell)
                    elif normalized_cell.isdigit() and normalized_cell != "0":
                        row_chars.append(normalized_cell)
                    else:
                        raise ValueError(
                            f"Puzzle cell at row {row_index+1}, column {col_index+1} must be a digit 1-9 or '.'."
                        )
                puzzle_rows.append("".join(row_chars))
        elif all(isinstance(row, str) for row in puzzle):
            puzzle_rows = []
            for idx, row in enumerate(puzzle):
                if not isinstance(row, str):
                    raise ValueError(f"Puzzle row {idx+1} is not a string.")
                row = row.strip().replace("0", ".")
                if len(row) != 9:
                    raise ValueError(f"Puzzle row {idx+1} must be exactly 9 characters, got {len(row)}: '{row}'")
                puzzle_rows.append(row)
        else:
            raise ValueError("Puzzle must be a list of 9 rows, each either an array of 9 cells or a 9-character string.")
    elif isinstance(puzzle, str):
        puzzle_str = puzzle.strip()
        if len(puzzle_str) == 81 and re.fullmatch(r"[0-9.]{81}", puzzle_str):
            puzzle_rows = [puzzle_str[i * 9 : (i + 1) * 9] for i in range(9)]
        else:
            puzzle_rows = _parse_board_string(puzzle_str)
    else:
        raise ValueError("Puzzle must be a nested array of rows or a single string board.")

    board = _parse_puzzle(puzzle_rows)
    _validate_initial_board(board)

    if not _solve(board):
        raise ValueError("Unable to solve the provided Sudoku puzzle. The initial board may be invalid or unsolvable.")

    solution = ["".join(str(cell) for cell in row) for row in board]
    return {"solution": solution}


def _parse_board_string(board_text: str) -> List[str]:
    rows: List[str] = []
    for raw_line in board_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("+") or stripped.startswith("-"):
            continue
        cleaned = re.sub(r"[|+\-\s]", "", stripped).replace("0", ".")
        if cleaned:
            rows.append(cleaned)

    if len(rows) != 9 or any(len(row) != 9 for row in rows):
        raise ValueError(
            "If puzzle is a string, it must be either an 81-character board or a multiline 9x9 board with optional separators."
        )
    return rows


def _parse_puzzle(rows: List[str]) -> List[List[int]]:
    board: List[List[int]] = []
    for row in rows:
        if not isinstance(row, str) or len(row) != 9:
            raise ValueError("Each puzzle row must be a string with exactly 9 characters.")
        parsed_row = []
        for char in row:
            if char in {".", "0"}:
                parsed_row.append(0)
            elif char.isdigit() and char != "0":
                parsed_row.append(int(char))
            else:
                raise ValueError("Puzzle rows may only contain digits 1-9, 0, or .")
        board.append(parsed_row)
    return board


def _validate_initial_board(board: List[List[int]]) -> None:
    duplicate_error = _find_duplicate(board)
    if duplicate_error is not None:
        raise ValueError(duplicate_error)


def _find_duplicate(board: List[List[int]]) -> Optional[str]:
    for row in range(9):
        seen: Dict[int, List[int]] = defaultdict(list)
        for col, value in enumerate(board[row]):
            if value != 0:
                seen[value].append(col)
        for value, cols in seen.items():
            if len(cols) > 1:
                positions = ", ".join(f"column {col + 1}" for col in cols)
                return (
                    f"Invalid puzzle: duplicate value {value} found in row {row + 1} at {positions}."
                )

    for col in range(9):
        seen: Dict[int, List[int]] = defaultdict(list)
        for row in range(9):
            value = board[row][col]
            if value != 0:
                seen[value].append(row)
        for value, rows in seen.items():
            if len(rows) > 1:
                positions = ", ".join(f"row {row + 1}" for row in rows)
                return (
                    f"Invalid puzzle: duplicate value {value} found in column {col + 1} at {positions}."
                )

    for box_row in range(3):
        for box_col in range(3):
            seen: Dict[int, List[tuple[int, int]]] = defaultdict(list)
            for row in range(box_row * 3, box_row * 3 + 3):
                for col in range(box_col * 3, box_col * 3 + 3):
                    value = board[row][col]
                    if value != 0:
                        seen[value].append((row, col))
            for value, coords in seen.items():
                if len(coords) > 1:
                    positions = ", ".join(
                        f"(row {r + 1}, column {c + 1})" for r, c in coords
                    )
                    return (
                        f"Invalid puzzle: duplicate value {value} found in 3x3 box starting at row {box_row * 3 + 1}, column {box_col * 3 + 1} at positions {positions}."
                    )

    return None


def _solve(board: List[List[int]]) -> bool:
    empty = _find_empty(board)
    if not empty:
        return True
    row, col = empty

    for value in range(1, 10):
        if _can_place(board, row, col, value):
            board[row][col] = value
            if _solve(board):
                return True
            board[row][col] = 0

    return False


def _find_empty(board: List[List[int]]) -> Optional[Tuple[int, int]]:
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                return row, col
    return None


def _can_place(board: List[List[int]], row: int, col: int, value: int) -> bool:
    if any(board[row][i] == value for i in range(9)):
        return False
    if any(board[i][col] == value for i in range(9)):
        return False

    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == value:
                return False

    return True
