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

    def query_tool_input(self, prompt: str, tool_name: str, tool_schema: Dict[str, Any]) -> str:
        instruction = self._build_tool_input_instruction(prompt, tool_name, tool_schema)
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
                    "Only decide whether the prompt requires a tool and which tool should be used. "
                    "Do not perform schema-specific input normalization in this step. "
                    "If a tool is selected, tool_input may be {} here and will be normalized separately."
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
                    "Respond only with valid JSON and do not include any explanatory text outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Tool name: {tool_name}\n"
                    f"Tool input schema:\n{json.dumps(tool_schema, indent=2)}\n\n"
                    f"User prompt:\n{prompt}\n\n"
                    "Interpret the prompt and normalize the user input into the exact structure required by the schema. "
                    "Return only a JSON object that conforms to the schema. "
                    "Do not include any extra properties or comments."
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
