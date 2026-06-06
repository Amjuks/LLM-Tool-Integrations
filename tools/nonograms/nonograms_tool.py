from typing import Any, Dict, List, Tuple


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    row_clues = input_data.get("row_clues")
    col_clues = input_data.get("col_clues")

    _validate_clues(row_clues, col_clues)

    rows = len(row_clues)
    cols = len(col_clues)
    row_patterns = [_patterns_for_clue(clue, cols) for clue in row_clues]

    solution = _solve_nonogram(row_patterns, col_clues)
    if solution is None:
        raise ValueError("Unable to solve the provided Nonograms puzzle. Check row and column clues for consistency.")

    return {"solution": ["".join("X" if cell else "." for cell in row) for row in solution]}


def _validate_clues(row_clues: List[List[int]], col_clues: List[List[int]]) -> None:
    if not isinstance(row_clues, list) or not isinstance(col_clues, list):
        raise ValueError("row_clues and col_clues must be arrays of arrays of integers.")
    if len(row_clues) == 0 or len(col_clues) == 0:
        raise ValueError("row_clues and col_clues must each contain at least one clue line.")
    for idx, clue in enumerate(row_clues, start=1):
        if not isinstance(clue, list) or any(not isinstance(value, int) or value < 0 for value in clue):
            raise ValueError(f"Invalid row clue at index {idx}: each clue must be a list of non-negative integers.")
    for idx, clue in enumerate(col_clues, start=1):
        if not isinstance(clue, list) or any(not isinstance(value, int) or value < 0 for value in clue):
            raise ValueError(f"Invalid column clue at index {idx}: each clue must be a list of non-negative integers.")


def _patterns_for_clue(clue: List[int], length: int) -> List[List[bool]]:
    if sum(clue) + max(0, len(clue) - 1) > length:
        raise ValueError(f"Clue {clue} cannot fit in length {length}.")

    patterns: List[List[bool]] = []

    if not clue:
        return [[False] * length]

    def backtrack(segment_index: int, position: int, row: List[bool]) -> None:
        if segment_index == len(clue):
            gaps = length - len(row)
            if gaps < 0:
                return
            patterns.append(row + [False] * gaps)
            return

        run_length = clue[segment_index]
        remaining_data = sum(clue[segment_index:]) + (len(clue) - segment_index - 1)
        for start in range(position, length - remaining_data + 1):
            new_row = row + [False] * (start - len(row)) + [True] * run_length
            if segment_index < len(clue) - 1:
                new_row.append(False)
            backtrack(segment_index + 1, len(new_row), new_row)

    backtrack(0, 0, [])
    return patterns


def _line_matches_clue(line: List[bool], clue: List[int], complete: bool) -> bool:
    groups: List[int] = []
    current = 0
    for cell in line:
        if cell:
            current += 1
        elif current:
            groups.append(current)
            current = 0
    if current:
        groups.append(current)

    if complete:
        return groups == clue

    if len(groups) > len(clue):
        return False
    for index, group_length in enumerate(groups):
        if group_length > clue[index]:
            return False
    if len(groups) < len(clue) and line and line[-1]:
        return len(groups) <= len(clue)
    return True


def _solve_nonogram(row_patterns: List[List[List[bool]]], col_clues: List[List[int]]) -> List[List[bool]] | None:
    rows = len(row_patterns)
    cols = len(col_clues)
    solution: List[List[bool]] = []

    def backtrack(row_index: int) -> bool:
        if row_index == rows:
            for col_index in range(cols):
                column = [solution[r][col_index] for r in range(rows)]
                if not _line_matches_clue(column, col_clues[col_index], complete=True):
                    return False
            return True

        for pattern in row_patterns[row_index]:
            valid = True
            for col_index, value in enumerate(pattern):
                column_prefix = [solution[r][col_index] for r in range(row_index)] + [value]
                if not _line_matches_clue(column_prefix, col_clues[col_index], complete=False):
                    valid = False
                    break
            if not valid:
                continue
            solution.append(pattern)
            if backtrack(row_index + 1):
                return True
            solution.pop()
        return False

    if backtrack(0):
        return solution
    return None
