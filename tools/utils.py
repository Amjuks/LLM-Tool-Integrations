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


def normalize_sudoku_tool_input(prompt: str, tool_input: dict) -> dict:
    puzzle = tool_input.get("puzzle")
    if not isinstance(puzzle, list) or len(puzzle) != 9:
        return tool_input

    if any(not isinstance(row, str) or len(row) != 9 for row in puzzle):
        return tool_input

    raw = extract_sudoku_string(prompt)
    if not raw:
        return tool_input

    puzzle_rows = [raw[i * 9 : (i + 1) * 9] for i in range(9)]
    if "".join(puzzle) != raw:
        return {"puzzle": puzzle_rows}
    return tool_input
