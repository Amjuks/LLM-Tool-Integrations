import re

puzzle = [
    ['5','3','.','.','7','.','.','.','.'],
    ['6','.','.','1','9','5','.','.','.'],
    ['.','9','8','.','.','.','6','.','.'],
    ['8','.','.','.','6','.','.','3','.'],
    ['4','.','.','8','.','3','.','.','1'],
    ['7','.','.','.','2','.','.','.','6'],
    ['.','6','.','.','.','.','2','8','.'],
    ['.','.','.','4','1','9','.','.','5'],
    ['.','.','.','.','8','.','.','7','9']
]

puzzle_rows = []
for row_index, row in enumerate(puzzle):
    if not isinstance(row, list):
        raise ValueError('row not list')
    if len(row) != 9:
        raise ValueError(f'row {row_index+1} len {len(row)}')
    row_chars = []
    for col_index, cell in enumerate(row):
        if not isinstance(cell, str) or len(cell) != 1:
            raise ValueError(f'cell {row_index+1},{col_index+1} invalid {cell!r}')
        normalized_cell = cell if cell != '0' else '.'
        if normalized_cell == '.':
            row_chars.append(normalized_cell)
        elif normalized_cell.isdigit() and normalized_cell != '0':
            row_chars.append(normalized_cell)
        else:
            raise ValueError(f'cell {row_index+1},{col_index+1} not digit/dot')
    puzzle_rows.append(''.join(row_chars))

print('puzzle_rows list path:')
for r in puzzle_rows:
    print(repr(r))

board_str = (
    "+-------+-------+-------+\n"
    "| 5 3 . | . 7 . | . . . |\n"
    "| 6 . . | 1 9 5 | . . . |\n"
    "| . 9 8 | . . . | . 6 . |\n"
    "+-------+-------+-------+\n"
    "| 8 . . | . 6 . | . . 3 |\n"
    "| 4 . . | 8 . 3 | . . 1 |\n"
    "| 7 . . | . 2 . | . . 6 |\n"
    "+-------+-------+-------+\n"
    "| . 6 . | . . . | 2 8 . |\n"
    "| . . . | 4 1 9 | . . 5 |\n"
    "| . . . | . 8 . | . 7 9 |\n"
    "+-------+-------+-------+"
)

cleaned_rows = []
for raw_line in board_str.splitlines():
    stripped = raw_line.strip()
    if not stripped or stripped.startswith('+') or stripped.startswith('-'):
        continue
    cleaned = re.sub(r'[|+\-\s]', '', stripped).replace('0', '.')
    if cleaned:
        cleaned_rows.append(cleaned)
print('puzzle_rows string path:')
for r in cleaned_rows:
    print(repr(r))
