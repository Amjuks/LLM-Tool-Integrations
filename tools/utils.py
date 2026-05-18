import re

STYLES = {
    "reset": "\033[0m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}


def color(text: str, style: str) -> str:
    return f"{STYLES.get(style, STYLES['reset'])}{text}{STYLES['reset']}"


def print_stage(title: str, message: str) -> None:
    print(color(f"[{title}]", "yellow"), message)


def extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def extract_sudoku_string(text: str) -> str | None:
    """Extract the first 81-character Sudoku sequence from the text."""
    match = re.search(r"[0-9.]{81,}", text)
    if match:
        return match.group(0)[:81]

    compact = "".join(ch for ch in text if ch in "0123456789.")
    if len(compact) >= 81:
        return compact[:81]
    return None


def _normalize_sudoku_cell(cell: str) -> str:
    value = cell.strip()
    if not value or value == "." or value == "0":
        return "."
    if value[0] in "123456789":
        return value[0]
    return "."


def parse_sudoku_markdown_table(text: str) -> list[str] | None:
    rows: list[str] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        if re.fullmatch(r"[\s|:\-]+", line):
            continue

        parts = line.split("|")
        if parts and parts[0].strip() == "" and parts[-1].strip() == "":
            parts = parts[1:-1]

        if len(parts) != 9:
            continue

        row = "".join(_normalize_sudoku_cell(part) for part in parts)
        if len(row) == 9:
            rows.append(row)

    return rows if len(rows) == 9 else None


def parse_sudoku_rows(text: str) -> list[str] | None:
    board = parse_sudoku_markdown_table(text)
    if board:
        return board

    raw = extract_sudoku_string(text)
    if raw and len(raw) == 81:
        return [raw[i * 9 : (i + 1) * 9] for i in range(9)]

    candidate: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cells = re.findall(r"[0-9.]", line)
        if len(cells) == 9:
            candidate.append("".join(cells))
    if len(candidate) >= 9:
        return candidate[:9]

    return None
