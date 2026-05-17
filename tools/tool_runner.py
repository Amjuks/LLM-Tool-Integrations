import importlib
import json
from pathlib import Path
from typing import Any, Dict

from tools.validators import validate_schema


class ToolRunner:
    def __init__(self, registry: Dict[str, Any]) -> None:
        self.registry = registry

    @staticmethod
    def load_registry() -> Dict[str, Any]:
        root = Path(__file__).resolve().parent
        registry_path = root / "registry.json"
        with registry_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _find_tool(self, tool_name: str) -> Dict[str, Any]:
        for tool in self.registry.get("tools", []):
            if tool.get("name") == tool_name:
                return tool
        raise ValueError(f"Tool '{tool_name}' is not registered.")

    def execute_tool(self, selection: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = selection["tool_name"]
        tool_input = selection["tool_input"]
        tool = self._find_tool(tool_name)

        validate_schema(tool_input, tool["input_schema"])
        module_name = tool.get("module")
        if not module_name:
            raise ValueError(f"Tool '{tool_name}' has no module configured.")

        module = importlib.import_module(module_name)
        if not hasattr(module, "run"):
            raise AttributeError(f"Tool module '{module_name}' does not expose a run(input_data) function.")

        result = module.run(tool_input)
        validate_schema(result, tool["output_schema"])
        return result
