# Python LLM Tool Ecosystem

A minimal Python-based LLM tool ecosystem with modular tool discovery, registry-driven dispatch, and an example Sudoku solver tool.

## Features

- Centralized `tools/registry.json` in strict JSON format
- Modular tool execution with per-tool schema validation
- OpenAI API support only
- Regex-safe JSON extraction from model responses
- Colored terminal pipeline logs

## Setup

1. Create a `.env` file from `.env.example`.
   - `OPENAI_BASE_URL=https://api.openai.com/v1`
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Tool Development

- Add a new tool under `tools/<tool-name>/`
- Register it in `tools/registry.json`
- Implement a `run(input_data: dict) -> dict` entrypoint

## Sudoku Example

The first tool is a Sudoku solver at `tools/sudoku/`. The tool accepts 9 rows of digits and blanks (`0` or `.`) and returns a completed Sudoku board.
