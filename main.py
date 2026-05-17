import json
import os
from pathlib import Path

from tools.llm_client import LLMClient
from tools.tool_runner import ToolRunner
from tools.utils import (
    color,
    extract_json_object,
    normalize_sudoku_tool_input,
    print_stage,
)
from tools.validators import validate_tool_dispatch


def load_tool_registry() -> dict:
    return ToolRunner.load_registry()


def main() -> None:
    print(color("AI Tool Ecosystem", "cyan"))
    print(color("Loading tool registry and model configuration...", "blue"))

    registry = load_tool_registry()
    llm = LLMClient()
    runner = ToolRunner(registry)

    while True:
        prompt = input(color("\nEnter prompt (or type EXIT to quit): ", "green")).strip()
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit", "q"}:
            print(color("Goodbye.", "blue"))
            break

        print_stage("User request", prompt)

        print_stage("Tool analysis phase", "Sending tool registry and user request to the LLM")
        analysis_response = llm.query_tool_selection(prompt, registry)
        print_stage("Tool analysis output", analysis_response)

        extracted = extract_json_object(analysis_response)
        if extracted is None:
            print(color("Failed to extract JSON from the tool analysis response.", "red"))
            continue

        try:
            selection = json.loads(extracted)
        except json.JSONDecodeError as exc:
            print(color(f"JSON decode error: {exc}", "red"))
            continue

        try:
            selection = validate_tool_dispatch(selection, registry)
        except ValueError as exc:
            print(color(f"Tool validation failed: {exc}", "red"))
            continue

        if not selection["tool_required"]:
            print_stage("Tool needed", "No")
            final_answer = llm.query_final_response(prompt, selection, None, analysis_response)
            print_stage("Final response", final_answer)
            continue

        if selection["tool_name"] == "sudoku_solver":
            normalized_input = normalize_sudoku_tool_input(prompt, selection["tool_input"])
            if normalized_input != selection["tool_input"]:
                selection["tool_input"] = normalized_input
                print_stage("Normalized puzzle input", json.dumps(normalized_input, indent=2))

        tool_name = selection["tool_name"]
        print_stage("Tool needed", "Yes")
        print_stage("Selected tool", tool_name)
        print_stage("Input payload", json.dumps(selection["tool_input"], indent=2))

        try:
            tool_result = runner.execute_tool(selection)
        except Exception as exc:
            error_message = str(exc)
            print(color(f"Tool execution failed: {error_message}", "red"))
            final_answer = llm.query_final_response(
                prompt,
                selection,
                None,
                analysis_response,
                tool_error=error_message,
            )
            print_stage("Final response", final_answer)
            continue

        print_stage("Tool execution result", json.dumps(tool_result, indent=2))

        final_answer = llm.query_final_response(prompt, selection, tool_result, analysis_response)
        print_stage("Final response", final_answer)


if __name__ == "__main__":
    main()
