import unittest

from tools.kakuro.kakuro_tool import run as run_kakuro
from tools.kenken.kenken_tool import run as run_kenken
from tools.hitori.hitori_tool import run as run_hitori
from tools.nonograms.nonograms_tool import run as run_nonograms
from tools.nurikabe.nurikabe_tool import run as run_nurikabe
from tools.star_battle.star_battle_tool import run as run_star_battle
from tools.sudoku.sudoku_tool import run as run_sudoku
from tools.tool_runner import ToolRunner


class HitoriToolTests(unittest.TestCase):
    def test_solve_trivial_all_unique_grid(self):
        grid = [
            "1234",
            "3412",
            "2143",
            "4321",
        ]
        result = run_hitori({"grid": grid})
        self.assertEqual(result["solution"], ["WWWW", "WWWW", "WWWW", "WWWW"])

    def test_invalid_hitori_input(self):
        with self.assertRaises(ValueError):
            run_hitori({"grid": []})


class KakuroToolTests(unittest.TestCase):
    def test_solve_simple_minimal_kakuro(self):
        cells = [
            ["r3c3", ".", "."],
            [".", "x", "x"],
            [".", "x", "x"],
        ]
        result = run_kakuro({"cells": cells})
        self.assertEqual(len(result["solution"]), 3)
        self.assertTrue(result["solution"][0].startswith(".1") or result["solution"][0].startswith(".2"))
        self.assertIn(result["solution"][1][0], {"1", "2"})
        self.assertIn(result["solution"][2][0], {"1", "2"})

    def test_invalid_kakuro_cell_format(self):
        with self.assertRaises(ValueError):
            run_kakuro({"cells": [["r3x", "."], [".", "x"]]})


class KenKenToolTests(unittest.TestCase):
    def test_solve_simple_3x3_kenken(self):
        cages = [
            {"cells": [{"row": 0, "col": 0}], "target": 1, "operation": "none"},
            {"cells": [{"row": 0, "col": 1}], "target": 2, "operation": "none"},
            {"cells": [{"row": 0, "col": 2}], "target": 3, "operation": "none"},
            {"cells": [{"row": 1, "col": 0}], "target": 2, "operation": "none"},
            {"cells": [{"row": 1, "col": 1}], "target": 3, "operation": "none"},
            {"cells": [{"row": 1, "col": 2}], "target": 1, "operation": "none"},
            {"cells": [{"row": 2, "col": 0}], "target": 3, "operation": "none"},
            {"cells": [{"row": 2, "col": 1}], "target": 1, "operation": "none"},
            {"cells": [{"row": 2, "col": 2}], "target": 2, "operation": "none"},
        ]
        result = run_kenken({"size": 3, "cages": cages})
        self.assertEqual(result["solution"], ["123", "231", "312"])

    def test_invalid_kenken_missing_cell(self):
        cages = [
            {"cells": [{"row": 0, "col": 0}], "target": 1, "operation": "none"},
        ]
        with self.assertRaises(ValueError):
            run_kenken({"size": 3, "cages": cages})


class NonogramsToolTests(unittest.TestCase):
    def test_solve_simple_cross_nonogram(self):
        row_clues = [[1], [3], [5], [3], [1]]
        col_clues = [[1], [3], [5], [3], [1]]
        expected = ["..X..", ".XXX.", "XXXXX", ".XXX.", "..X.."]
        result = run_nonograms({"row_clues": row_clues, "col_clues": col_clues})
        self.assertEqual(result["solution"], expected)

    def test_invalid_nonogram_clues(self):
        with self.assertRaises(ValueError):
            run_nonograms({"row_clues": [[1, -1]], "col_clues": [[1]]})


class NurikabeToolTests(unittest.TestCase):
    def test_solve_simple_nurikabe(self):
        grid = ["1..2", "....", ".2.1", "...."]
        result = run_nurikabe({"grid": grid})
        self.assertEqual(len(result["solution"]), 4)
        self.assertEqual(result["solution"][0][0], "1")
        self.assertEqual(result["solution"][0][3], "1")
        self.assertEqual(result["solution"][2][1], "1")
        self.assertEqual(result["solution"][2][3], "1")

    def test_parse_nurikabe_grid_with_spaces(self):
        grid = [
            "1 . . 2",
            " . . . . ",
            " . 2 . 1",
            " . . . . ",
        ]
        result = run_nurikabe({"grid": grid})
        self.assertEqual(len(result["solution"]), 4)
        self.assertTrue(all(len(row) == 4 for row in result["solution"]))
        self.assertTrue(all(ch in {"0", "1"} for row in result["solution"] for ch in row))

    def test_invalid_nurikabe_grid(self):
        with self.assertRaises(ValueError):
            run_nurikabe({"grid": ["1.0", "..1"]})


class StarBattleToolTests(unittest.TestCase):
    def test_solve_simple_star_battle(self):
        regions = [
            ["A", "A", "B", "B"],
            ["A", "A", "B", "B"],
            ["C", "C", "D", "D"],
            ["C", "C", "D", "D"],
        ]
        result = run_star_battle({"regions": regions, "stars_per_region": 1})
        self.assertEqual(len(result["solution"]), 4)
        self.assertEqual(sum(row.count("*") for row in result["solution"]), 4)
        self.assertEqual(result["solution"][0].count("*"), 1)
        self.assertEqual(result["solution"][1].count("*"), 1)
        self.assertEqual(result["solution"][2].count("*"), 1)
        self.assertEqual(result["solution"][3].count("*"), 1)

    def test_invalid_star_battle_regions(self):
        with self.assertRaises(ValueError):
            run_star_battle({"regions": [["A", ""], ["A", "A"]], "stars_per_region": 1})

    def test_solve_4x4_star_battle_two_stars(self):
        regions = [
            ["A", "A", "B", "B"],
            ["A", "A", "B", "B"],
            ["C", "C", "D", "D"],
            ["C", "C", "D", "D"],
        ]
        result = run_star_battle({"regions": regions, "stars_per_region": 2})
        self.assertEqual(len(result["solution"]), 4)
        row_counts = [row.count("*") for row in result["solution"]]
        self.assertEqual(row_counts, [2, 2, 2, 2])
        col_counts = [sum(row[c] == "*" for row in result["solution"]) for c in range(4)]
        self.assertEqual(col_counts, [2, 2, 2, 2])
        region_counts = {label: 0 for label in ["A", "B", "C", "D"]}
        for r, row in enumerate(result["solution"]):
            for c, ch in enumerate(row):
                if ch == "*":
                    region_counts[regions[r][c]] += 1
        self.assertEqual(region_counts, {"A": 2, "B": 2, "C": 2, "D": 2})


class SudokuToolTests(unittest.TestCase):
    def test_solve_nested_list_sudoku(self):
        puzzle = [
            ["5", "3", ".", ".", "7", ".", ".", ".", "."],
            ["6", ".", ".", "1", "9", "5", ".", ".", "."],
            [".", "9", "8", ".", ".", ".", ".", "6", "."],
            ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
            ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
            ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
            [".", "6", ".", ".", ".", ".", "2", "8", "."],
            [".", ".", ".", "4", "1", "9", ".", ".", "5"],
            [".", ".", ".", ".", "8", ".", ".", "7", "9"],
        ]
        result = run_sudoku({"puzzle": puzzle})
        self.assertEqual(result["solution"][0], "534678912")
        self.assertEqual(result["solution"][-1], "345286179")

    def test_solve_string_sudoku(self):
        board = (
            "53..7...."
            "6..195..."
            ".98....6."
            "8...6...3"
            "4..8.3..1"
            "7...2...6"
            ".6....28."
            "...419..5"
            "....8..79"
        )
        result = run_sudoku({"puzzle": board})
        self.assertEqual(result["solution"][0], "534678912")
        self.assertEqual(result["solution"][-1], "345286179")

    def test_invalid_sudoku_duplicate(self):
        puzzle = [
            ["1", "1", ".", ".", ".", ".", ".", ".", "."],
        ] * 9
        with self.assertRaises(ValueError):
            run_sudoku({"puzzle": puzzle})


class ToolRunnerTests(unittest.TestCase):
    def test_tool_runner_executes_all_registered_tools(self):
        registry = ToolRunner.load_registry()
        runner = ToolRunner(registry)
        samples = {
            "hitori_solver": {"grid": ["1234", "3412", "2143", "4321"]},
            "kakuro_solver": {"cells": [["r3c3", ".", "."], [".", "x", "x"], [".", "x", "x"]]},
            "kenken_solver": {
                "size": 3,
                "cages": [
                    {"cells": [{"row": 0, "col": 0}], "target": 1, "operation": "none"},
                    {"cells": [{"row": 0, "col": 1}], "target": 2, "operation": "none"},
                    {"cells": [{"row": 0, "col": 2}], "target": 3, "operation": "none"},
                    {"cells": [{"row": 1, "col": 0}], "target": 2, "operation": "none"},
                    {"cells": [{"row": 1, "col": 1}], "target": 3, "operation": "none"},
                    {"cells": [{"row": 1, "col": 2}], "target": 1, "operation": "none"},
                    {"cells": [{"row": 2, "col": 0}], "target": 3, "operation": "none"},
                    {"cells": [{"row": 2, "col": 1}], "target": 1, "operation": "none"},
                    {"cells": [{"row": 2, "col": 2}], "target": 2, "operation": "none"},
                ],
            },
            "nonograms_solver": {"row_clues": [[1], [3], [5], [3], [1]], "col_clues": [[1], [3], [5], [3], [1]]},
            "nurikabe_solver": {"grid": ["1..2", "....", ".2.1", "...."]},
            "star_battle_solver": {
                "regions": [
                    ["A", "A", "B", "B"],
                    ["A", "A", "B", "B"],
                    ["C", "C", "D", "D"],
                    ["C", "C", "D", "D"],
                ],
                "stars_per_region": 1,
            },
            "sudoku_solver": {"puzzle": [
                ["5", "3", ".", ".", "7", ".", ".", ".", "."],
                ["6", ".", ".", "1", "9", "5", ".", ".", "."],
                [".", "9", "8", ".", ".", ".", ".", "6", "."],
                ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
                ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
                ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
                [".", "6", ".", ".", ".", ".", "2", "8", "."],
                [".", ".", ".", "4", "1", "9", ".", ".", "5"],
                [".", ".", ".", ".", "8", ".", ".", "7", "9"],
            ]},
        }

        for tool_name, tool_input in samples.items():
            with self.subTest(tool=tool_name):
                result = runner.execute_tool({"tool_name": tool_name, "tool_input": tool_input})
                self.assertIn("solution", result)
                self.assertIsInstance(result["solution"], list)
                self.assertTrue(len(result["solution"]) > 0)


if __name__ == "__main__":
    unittest.main()
