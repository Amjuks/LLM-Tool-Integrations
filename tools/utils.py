import re
from typing import Any, Dict, List, Optional, Pattern, Tuple

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


def extract_json_object(text: str) -> Optional[str]:
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


def _parse_pattern_char_class(pattern: str) -> Optional[Tuple[int, str]]:
    if not isinstance(pattern, str):
        return None

    match = re.fullmatch(r"^\^?\[([^\]]+)\]\{(\d+)\}\$?$", pattern)
    if match:
        allowed_chars = match.group(1)
        length = int(match.group(2))
        return (length, allowed_chars)

    match = re.fullmatch(r"^\^?\[([^\]]+)\]\+\$?$", pattern)
    if match:
        allowed_chars = match.group(1)
        return (0, allowed_chars)

    match = re.fullmatch(r"^\^?\[([^\]]+)\]\$?$", pattern)
    if match:
        allowed_chars = match.group(1)
        return (1, allowed_chars)

    return None


def _fixed_length_row_schema_info(property_schema: Dict[str, Any]) -> Optional[Tuple[int, str]]:
    if property_schema.get("type") != "array":
        return None

    items = property_schema.get("items")
    if not isinstance(items, dict):
        return None

    item_type = items.get("type")
    if item_type == "string":
        pattern = items.get("pattern")
        info = _parse_pattern_char_class(pattern)
        if info is not None:
            return info

    if item_type == "array":
        nested_items = items.get("items")
        if isinstance(nested_items, dict) and nested_items.get("type") == "string":
            pattern = nested_items.get("pattern")
            info = _parse_pattern_char_class(pattern)
            if info is None:
                return None
            expected_row_length = items.get("minItems")
            if not isinstance(expected_row_length, int) or expected_row_length < 1:
                expected_row_length = items.get("maxItems")
            if not isinstance(expected_row_length, int) or expected_row_length < 1:
                return None
            return expected_row_length, info[1]

    return None


def _clean_grid_line(raw_line: str) -> str:
    return re.sub(r"[|+\-\s]", "", raw_line)


def _find_last_rows(rows: List[str], expected_count: int) -> Optional[List[str]]:
    if len(rows) < expected_count:
        return None
    return rows[-expected_count:]


def _extract_fixed_length_rows(prompt: str, expected_count: int, expected_length: int, allowed_chars: str) -> Optional[List[str]]:
    rows: List[str] = []
    pattern = re.compile(fr"^[{re.escape(allowed_chars)}]+$")

    for raw_line in prompt.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("+") or stripped.startswith("-"):
            continue

        cleaned = _clean_grid_line(stripped)
        if len(cleaned) != expected_length:
            continue
        if pattern.fullmatch(cleaned):
            rows.append(cleaned)

    if len(rows) == expected_count:
        return rows
    if len(rows) > expected_count:
        return _find_last_rows(rows, expected_count)

    rows = []
    for raw_line in prompt.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("+") or stripped.startswith("-"):
            continue
        cleaned = _clean_grid_line(stripped)
        if len(cleaned) != expected_length:
            continue
        rows.append(cleaned)
    if len(rows) == expected_count:
        return rows
    if len(rows) > expected_count:
        return _find_last_rows(rows, expected_count)

    return None


def _extract_board_string(prompt: str) -> Optional[str]:
    rows: List[str] = []
    for raw_line in prompt.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("+") or stripped.startswith("-"):
            continue
        cleaned = _clean_grid_line(stripped)
        if not cleaned:
            continue
        rows.append(cleaned)

    if not rows:
        return None

    lengths = {len(row) for row in rows}
    if len(lengths) != 1:
        return None
    if len(rows) == 9:
        return "\n".join(rows)
    if len(rows) > 9:
        return "\n".join(_find_last_rows(rows, 9))

    return None


def _normalize_sudoku_cell(char: str) -> str:
    if char == "0":
        return "."
    return char


def _rows_to_nested_cells(rows: List[str]) -> List[List[str]]:
    return [[_normalize_sudoku_cell(char) for char in row] for row in rows]


def try_prenormalize_tool_input(prompt: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if schema.get("type") != "object":
        return None

    normalized: Dict[str, Any] = {}
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return None

    for name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            continue

        fixed_info = _fixed_length_row_schema_info(prop_schema)
        if fixed_info is not None:
            expected_length, allowed_chars = fixed_info
            expected_rows = prop_schema.get("minItems")
            if isinstance(expected_rows, int) and expected_rows > 0 and expected_length > 0:
                rows = _extract_fixed_length_rows(prompt, expected_rows, expected_length, allowed_chars)
                if rows is not None:
                    normalized[name] = _rows_to_nested_cells(rows)
            continue

        if prop_schema.get("type") == "string" and name in {"puzzle", "board", "grid"}:
            board_text = _extract_board_string(prompt)
            if board_text is not None:
                normalized[name] = board_text

    if normalized:
        return normalized
    return None
