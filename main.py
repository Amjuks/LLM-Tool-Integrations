import json
import os
from pathlib import Path

from tools.llm_client import LLMClient
from tools.tool_runner import ToolRunner
from tools.utils import (
    color,
    extract_json_object,
    parse_sudoku_rows,
    print_stage,
)
from tools.validators import validate_schema, validate_tool_dispatch


def load_tool_registry() -> dict:
    return ToolRunner.load_registry()


def main() -> None:
    print(color("AI Tool Ecosystem", "cyan"))
    print(color("Loading tool registry and model configuration...", "blue"))

    registry = load_tool_registry()
    llm = LLMClient()
    runner = ToolRunner(registry)

    def read_multiline_prompt() -> str:
        print(color("\nEnter prompt (or type EXIT to quit). Finish with an empty line:", "green"))
        lines: list[str] = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "":
                break
            lines.append(line)

        prompt_text = "\n".join(lines).strip()
        return prompt_text

    while True:
        prompt = read_multiline_prompt()
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

        tool_name = selection["tool_name"]
        tool = next((tool for tool in registry.get("tools", []) if tool.get("name") == tool_name), None)
        if tool is None:
            print(color(f"Selected tool '{tool_name}' is not registered.", "red"))
            continue

        tool_schema = tool["input_schema"]
        print_stage("Tool needed", "Yes")
        print_stage("Selected tool", tool_name)

        if tool_name == "sudoku_solver":
            parsed_rows = parse_sudoku_rows(prompt)
            if parsed_rows is not None:
                selection["tool_input"] = {"puzzle": parsed_rows}
                print_stage("Tool input normalization", "Parsed Sudoku board from prompt locally")
                print_stage("Input payload", json.dumps(selection["tool_input"], indent=2))
            else:
                print_stage("Tool input normalization", "Normalizing user prompt into the selected tool schema")
                tool_input_response = llm.query_tool_input(prompt, tool_name, tool_schema)
                print_stage("Normalized tool input output", tool_input_response)

                normalized_json = extract_json_object(tool_input_response)
                if normalized_json is None:
                    print(color("Failed to extract JSON from the tool input normalization response.", "red"))
                    continue

                try:
                    tool_input = json.loads(normalized_json)
                except json.JSONDecodeError as exc:
                    print(color(f"JSON decode error: {exc}", "red"))
                    continue

                try:
                    validate_schema(tool_input, tool_schema)
                except ValueError as exc:
                    print(color(f"Tool input normalization failed schema validation: {exc}", "red"))
                    continue

                selection["tool_input"] = tool_input
                print_stage("Input payload", json.dumps(selection["tool_input"], indent=2))
        else:
            print_stage("Tool input normalization", "Normalizing user prompt into the selected tool schema")
            tool_input_response = llm.query_tool_input(prompt, tool_name, tool_schema)
            print_stage("Normalized tool input output", tool_input_response)

            normalized_json = extract_json_object(tool_input_response)
            if normalized_json is None:
                print(color("Failed to extract JSON from the tool input normalization response.", "red"))
                continue

            try:
                tool_input = json.loads(normalized_json)
            except json.JSONDecodeError as exc:
                print(color(f"JSON decode error: {exc}", "red"))
                continue

            try:
                validate_schema(tool_input, tool_schema)
            except ValueError as exc:
                print(color(f"Tool input normalization failed schema validation: {exc}", "red"))
                continue

            selection["tool_input"] = tool_input
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
