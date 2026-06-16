import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from tools.session_logger import SessionLogger


class LLMClient:
    def __init__(self, logger: Optional[SessionLogger] = None) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.logger = logger

        if not self.api_key:
            raise EnvironmentError("OPENAI_API_KEY is required. Copy .env.example to .env and set the API key.")

        client_args = {"api_key": self.api_key}
        if self.base_url:
            client_args["base_url"] = self.base_url

        self.client = OpenAI(**client_args)

    def query_tool_selection(
        self,
        prompt: str,
        registry: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        instruction = self._build_tool_selection_instruction(prompt, registry)
        response = self._send_chat_request(instruction, history)
        return response

    def query_tool_input(
        self,
        prompt: str,
        tool_name: str,
        tool_schema: Dict[str, Any],
        previous_response: Optional[str] = None,
        validation_errors: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        if previous_response is None:
            instruction = self._build_tool_input_instruction(prompt, tool_name, tool_schema)
        else:
            instruction = self._build_tool_input_correction_instruction(
                prompt,
                tool_name,
                tool_schema,
                previous_response,
                validation_errors,
            )
        response = self._send_chat_request(instruction, history)
        return response

    def query_final_response(
        self,
        prompt: str,
        selection: Optional[Dict[str, Any]],
        tool_output: Optional[Dict[str, Any]],
        analysis_response: str,
        tool_error: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an assistant that produces professional final responses. "
                    "Use the completed tool output if a tool was used."
                ),
            },
            {
                "role": "user",
                "content": self._build_final_response_instruction(
                    prompt, selection, tool_output, analysis_response, tool_error
                ),
            },
        ]
        return self._send_chat_request(messages, history)

    def _build_tool_selection_instruction(self, prompt: str, registry: Dict[str, Any]) -> list[dict[str, str]]:
        tool_list = json.dumps(registry, indent=2)
        return [
            {
                "role": "system",
                "content": (
                    "You are a tool selection agent. The user will provide a prompt and a tool registry. "
                    "Decide whether a tool is required. Respond only with valid JSON. "
                    "Do not include explanatory text outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Available tools and schemas:\n" + tool_list + "\n\n"
                    "User prompt:\n" + prompt + "\n\n"
                    "Return JSON with the following fields:\n"
                    "- tool_required: true or false\n"
                    "- tool_name: the tool name if required, otherwise null\n"
                    "- tool_input: an object matching the tool input schema if a tool is required, otherwise {}\n\n"
                    "If a tool is required, include a fully normalized tool_input object that conforms to the selected tool's schema. "
                    "Validate the tool_input against the schema before returning it. "
                    "For board-like puzzles, preserve every cell and return exactly the required row lengths and characters. "
                    "Do not include any explanatory text outside the JSON object. "
                    "If the prompt does not require a tool, set tool_name to null and tool_input to {}."
                ),
            },
        ]

    def _build_tool_input_instruction(
        self,
        prompt: str,
        tool_name: str,
        tool_schema: Dict[str, Any],
    ) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are a tool input normalizer. You will receive a user prompt, the name of a selected tool, "
                    "and the tool's exact input schema. Your job is to return a JSON object that exactly matches the schema. "
                    "Respond only with valid JSON and do not include any explanatory text, markdown, or code fences."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Tool name: {tool_name}\n"
                    f"Tool input schema:\n{json.dumps(tool_schema, indent=2)}\n\n"
                    f"User prompt:\n{prompt}\n\n"
                    "Interpret the prompt and normalize the user input into the exact structure required by the schema. "
                    "Return only a JSON object that conforms exactly to the schema, with all required fields present. "
                    "If the user prompt contains a drawn board or grid with separators (such as |, +, -, spaces), ignore those characters and map the data into the schema fields. "
                    "For Sudoku, return exactly one field named puzzle, and make it an array of 9 arrays of 9 strings. "
                    "Each string must be a single character: digits 1-9, '.' or '0' for blank cells. "
                    "If the prompt includes a parsed board section, use those values exactly. "
                    "Do not include any extra properties, comments, or text outside the JSON object."
                ),
            },
        ]

    def _build_tool_input_correction_instruction(
        self,
        prompt: str,
        tool_name: str,
        tool_schema: Dict[str, Any],
        previous_response: str,
        validation_errors: Optional[str],
    ) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are a tool input normalizer. A previous attempt to format the input failed validation. "
                    "You must now return a corrected JSON object that exactly matches the schema. "
                    "Respond only with valid JSON and do not include any explanatory text, markdown, or code fences."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Tool name: {tool_name}\n"
                    f"Tool input schema:\n{json.dumps(tool_schema, indent=2)}\n\n"
                    f"User prompt:\n{prompt}\n\n"
                    "Previous tool input output:\n"
                    f"{previous_response}\n\n"
                    "Validation errors:\n"
                    f"{validation_errors}\n\n"
                    "Produce a corrected JSON object that conforms exactly to the tool schema. "
                    "Use the exact schema field names and convert any drawn board, separator-based grid, or natural language clues into the required JSON structure. "
                    "For Sudoku, the puzzle field must be an array of 9 arrays of 9 strings, each string being a single digit 1-9, '.' or '0'. "
                    "If the prompt includes a parsed board section, use those values exactly. "
                    "Do not infer fields beyond those defined by the tool schema. "
                    "Do not include any extra properties, comments, or text outside the JSON object."
                ),
            },
        ]

    def _build_final_response_instruction(
        self,
        prompt: str,
        selection: Optional[Dict[str, Any]],
        tool_output: Optional[Dict[str, Any]],
        analysis_response: str,
        tool_error: Optional[str] = None,
    ) -> str:
        payload = {
            "original_prompt": prompt,
            "tool_decision": selection,
            "tool_output": tool_output,
            "tool_analysis": analysis_response,
            "tool_error": tool_error,
        }
        return (
            "Use the following data to produce a final answer for the user. "
            "If a tool output is available, integrate it into the response. "
            "If there was an error during tool execution, include the exact tool_error string verbatim and explain it in context. "
            "Do not invent additional tool results. "
            "Do not soften or paraphrase the precise tool failure details.\n\n"
            + json.dumps(payload, indent=2)
        )

    def _send_chat_request(
        self,
        messages: List[Dict[str, str]],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        combined_messages = []
        if history:
            combined_messages.extend(history)
        combined_messages.extend(messages)

        if self.logger is not None:
            self.logger.log_event("openai_api_request", {
                "model": self.model,
                "messages": combined_messages,
                "temperature": 0,
                "max_tokens": 800,
            })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=combined_messages,
            temperature=0,
            max_tokens=800,
        )

        response_payload = {
            "model": getattr(response, "model", None),
            "usage": getattr(response, "usage", None),
            "content": response.choices[0].message.content.strip() if response.choices else None,
        }
        if self.logger is not None:
            self.logger.log_event("openai_api_response", response_payload)

        return response.choices[0].message.content.strip()
