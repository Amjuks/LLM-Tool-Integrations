import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

        if not self.api_key:
            raise EnvironmentError("OPENAI_API_KEY is required. Copy .env.example to .env and set the API key.")

        client_args = {"api_key": self.api_key}
        if self.base_url:
            client_args["base_url"] = self.base_url

        self.client = OpenAI(**client_args)

    def query_tool_selection(self, prompt: str, registry: Dict[str, Any]) -> str:
        instruction = self._build_tool_selection_instruction(prompt, registry)
        response = self._send_chat_request(instruction)
        return response

    def query_final_response(
        self,
        prompt: str,
        selection: Dict[str, Any] | None,
        tool_output: Dict[str, Any] | None,
        analysis_response: str,
        tool_error: str | None = None,
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
        return self._send_chat_request(messages)

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
                    "- tool_input: object matching the selected tool input schema or {}\n\n"
                    "If the user provides a Sudoku puzzle in any format (single string, grid, or list), always convert it to a list of 9 strings, each exactly 9 characters, using only digits 1-9 and dots (.) for blanks. "
                    "Preserve the exact character order of the original puzzle when normalizing rows. Do not add, remove, or alter any digits. "
                    "If a row is too short, pad with dots at the end. If a row is too long, truncate to 9 characters. "
                    "If the original input is a single 81-character puzzle string, the concatenation of the 9 rows must equal that exact string. "
                    "If the provided board is invalid or unsolvable, do not force a solve. Instead, return a tool error or require a valid puzzle."
                ),
            },
        ]

    def _build_final_response_instruction(
        self,
        prompt: str,
        selection: Dict[str, Any] | None,
        tool_output: Dict[str, Any] | None,
        analysis_response: str,
        tool_error: str | None = None,
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
            "If there was an error during tool execution, explain it clearly and professionally. "
            "Do not invent additional tool results.\n\n"
            + json.dumps(payload, indent=2)
        )

    def _send_chat_request(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
