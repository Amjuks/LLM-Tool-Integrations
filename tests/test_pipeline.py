import unittest

from tools.utils import extract_json_object
from tools.validators import validate_tool_dispatch


class PipelineTests(unittest.TestCase):
    def test_validate_tool_dispatch_preserves_tool_input(self):
        registry = {"tools": [{"name": "sudoku_solver"}]}
        selection = {
            "tool_required": True,
            "tool_name": "sudoku_solver",
            "tool_input": {"puzzle": ["123456789" * 1] * 9},
        }
        validated = validate_tool_dispatch(selection, registry)
        self.assertTrue(validated["tool_required"])
        self.assertEqual(validated["tool_name"], "sudoku_solver")
        self.assertEqual(validated["tool_input"], selection["tool_input"])

    def test_validate_tool_dispatch_handles_missing_tool_input(self):
        registry = {"tools": [{"name": "nonograms_solver"}]}
        selection = {
            "tool_required": True,
            "tool_name": "nonograms_solver",
        }
        validated = validate_tool_dispatch(selection, registry)
        self.assertTrue(validated["tool_required"])
        self.assertEqual(validated["tool_input"], {})

    def test_validate_tool_dispatch_rejects_invalid_tool_input_type(self):
        registry = {"tools": [{"name": "hitori_solver"}]}
        selection = {
            "tool_required": True,
            "tool_name": "hitori_solver",
            "tool_input": "not an object",
        }
        with self.assertRaises(ValueError):
            validate_tool_dispatch(selection, registry)

    def test_try_prenormalize_tool_input_sudoku_grid(self):
        from tools.utils import try_prenormalize_tool_input

        prompt = """Solve this:+-------+-------+-------+\n| 5 3 . | . 7 . | . . . |\n| 6 . . | 1 9 5 | . . . |\n| . 9 8 | . . . | . 6 . |\n+-------+-------+-------+\n| 8 . . | . 6 . | . . 3 |\n| 4 . . | 8 . 3 | . . 1 |\n| 7 . . | . 2 . | . . 6 |\n+-------+-------+-------+\n| . 6 . | . . . | 2 8 . |\n| . . . | 4 1 9 | . . 5 |\n| . . . | . 8 . | . 7 9 |\n+-------+-------+-------+"""
        schema = {
            "type": "object",
            "properties": {
                "puzzle": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^[0-9.]{9}$"},
                    "minItems": 9,
                    "maxItems": 9,
                }
            },
            "required": ["puzzle"],
            "additionalProperties": False,
        }

        normalized = try_prenormalize_tool_input(prompt, schema)
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized["puzzle"][0], ["5", "3", ".", ".", "7", ".", ".", ".", "."])
        self.assertEqual(len(normalized["puzzle"]), 9)

    def test_try_prenormalize_tool_input_sudoku_grid_with_duplicate_prompt(self):
        from tools.utils import try_prenormalize_tool_input

        prompt = """Finish with an empty line:
| 5 3 . | . 7 . | . . . |
| 6 . . | 1 9 5 | . . . |
| . 9 8 | . . . | . 6 . |
+-------+-------+-------+
| 8 . . | . 6 . | . . 3 |
| 4 . . | 8 . 3 | . . 1 |
| 7 . . | . 2 . | . . 6 |
+-------+-------+-------+
| . 6 . | . . . | 2 8 . |
| . . . | 4 1 9 | . . 5 |
| . . . | . 8 . | . 7 9 |
+-------+-------+-------+

[User request] Solve this: +-------+-------+-------+
| 5 3 . | . 7 . | . . . |
| 6 . . | 1 9 5 | . . . |
| . 9 8 | . . . | . 6 . |
+-------+-------+-------+
| 8 . . | . 6 . | . . 3 |
| 4 . . | 8 . 3 | . . 1 |
| 7 . . | . 2 . | . . 6 |
+-------+-------+-------+
| . 6 . | . . . | 2 8 . |
| . . . | 4 1 9 | . . 5 |
| . . . | . 8 . | . 7 9 |
+-------+-------+-------+"""
        schema = {
            "type": "object",
            "properties": {
                "puzzle": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^[0-9.]$"},
                        "minItems": 9,
                        "maxItems": 9,
                    },
                    "minItems": 9,
                    "maxItems": 9,
                }
            },
            "required": ["puzzle"],
            "additionalProperties": False,
        }

        normalized = try_prenormalize_tool_input(prompt, schema)
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized["puzzle"][0], ["5", "3", ".", ".", "7", ".", ".", ".", "."])
        self.assertEqual(normalized["puzzle"][2], [".", "9", "8", ".", ".", ".", ".", "6", "."])
        self.assertEqual(len(normalized["puzzle"]), 9)

    def test_extract_json_object_with_wrapped_text(self):
        text = "Here is the result: {\"foo\": \"bar\"} and more text."
        extracted = extract_json_object(text)
        self.assertEqual(extracted, '{"foo": "bar"}')

    def test_sudoku_solver_solves_prompt_board_string(self):
        from tools.sudoku.sudoku_tool import run

        board = (
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

        result = run({"puzzle": board})
        self.assertIn("solution", result)
        self.assertEqual(result["solution"][0], "534678912")
        self.assertEqual(result["solution"][-1], "345286179")


if __name__ == "__main__":
    unittest.main()
