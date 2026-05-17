from typing import Any, Dict, List


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:

    puzzle = input_data.get("puzzle")
    # Accept a single string of 81 chars or a list of 9 strings
    if isinstance(puzzle, str):
        if len(puzzle) != 81:
            raise ValueError("If puzzle is a string, it must be exactly 81 characters.")
        puzzle_rows = [puzzle[i*9:(i+1)*9] for i in range(9)]
    elif isinstance(puzzle, list) and len(puzzle) == 9:
        # Normalize: trim whitespace and check length
        puzzle_rows = []
        for idx, row in enumerate(puzzle):
            if not isinstance(row, str):
                raise ValueError(f"Puzzle row {idx+1} is not a string.")
            row = row.strip()
            if len(row) != 9:
                raise ValueError(f"Puzzle row {idx+1} must be exactly 9 characters, got {len(row)}: '{row}'")
            puzzle_rows.append(row)
    else:
        raise ValueError("Puzzle must be a single 81-character string or a list of 9 strings of length 9.")

    board = _parse_puzzle(puzzle_rows)
    _validate_initial_board(board)

    if not _solve(board):
        raise ValueError("Unable to solve the provided Sudoku puzzle. The initial board may be invalid or unsolvable.")

    solution = ["".join(str(cell) for cell in row) for row in board]
    return {"solution": solution}


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
    for index in range(9):
        row_values = [value for value in board[index] if value != 0]
        if len(row_values) != len(set(row_values)):
            raise ValueError(f"Invalid puzzle: duplicate value found in row {index + 1}.")

        col_values = [board[r][index] for r in range(9) if board[r][index] != 0]
        if len(col_values) != len(set(col_values)):
            raise ValueError(f"Invalid puzzle: duplicate value found in column {index + 1}.")

    for box_row in range(3):
        for box_col in range(3):
            box_values: List[int] = []
            for row in range(box_row * 3, box_row * 3 + 3):
                for col in range(box_col * 3, box_col * 3 + 3):
                    value = board[row][col]
                    if value != 0:
                        box_values.append(value)
            if len(box_values) != len(set(box_values)):
                raise ValueError(
                    f"Invalid puzzle: duplicate value found in 3x3 box starting at row {box_row * 3 + 1}, column {box_col * 3 + 1}."
                )


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


def _find_empty(board: List[List[int]]) -> tuple[int, int] | None:
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
