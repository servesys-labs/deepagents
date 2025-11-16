"""Middleware to enforce AvocadoDB exclusivity.

When the agent calls avocado_compile_context, this middleware blocks
all other read-oriented tools (read_file, grep, ls) from running in parallel.

This ensures deterministic, AvocadoDB-first behavior.
"""

from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig


class AvocadoDBExclusivityMiddleware(AgentMiddleware):
    """Middleware that enforces AvocadoDB-only execution for codebase queries.

    When avocado_compile_context is called, blocks these tools:
    - read_file
    - grep
    - ls
    - glob

    This prevents the agent from calling multiple tools in parallel,
    ensuring AvocadoDB is used exclusively for codebase questions.
    """

    # Track if we've seen avocado in this turn
    _has_avocado_this_turn: bool = False

    def __init__(self):
        """Initialize middleware."""
        super().__init__()
        # Tools to block when avocado_compile_context is active
        self.blocked_tools = {"read_file", "grep", "ls", "glob"}
        self._blocked_this_turn = []

    def wrap_tool_call(self, tool_call: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
        """Intercept tool calls and block read tools when AvocadoDB is present.

        This is called for EACH tool call before execution.
        """
        # First pass: check if avocado_compile_context is in this batch
        # (This is a simplification - in reality we'd need to look at all pending calls)
        tool_name = tool_call.get("name", "")

        # If this is avocado_compile_context, mark it
        if tool_name == "avocado_compile_context":
            self._has_avocado_this_turn = True
            return tool_call

        # If we've seen avocado and this is a blocked tool, filter it out
        if self._has_avocado_this_turn and tool_name in self.blocked_tools:
            if tool_name not in self._blocked_this_turn:
                self._blocked_this_turn.append(tool_name)
            # Return None or raise to skip this tool
            # Actually, we can't skip easily here, so let's use a different approach
            return tool_call

        return tool_call

    async def __call__(
        self,
        state: dict[str, Any],
        config: RunnableConfig,
        *,
        store: Any,
    ) -> dict[str, Any]:
        """Pre-process state to filter tool calls before execution."""
        messages = state.get("messages", [])

        if not messages:
            return state

        last_message = messages[-1]

        # Check if this is an AI message with tool calls
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state

        tool_calls = list(last_message.tool_calls)

        # Check if avocado_compile_context is being called
        has_avocado = any(
            tc.get("name") == "avocado_compile_context"
            for tc in tool_calls
        )

        if has_avocado:
            # Filter out blocked tools
            filtered_calls = [
                tc for tc in tool_calls
                if tc.get("name") == "avocado_compile_context"
                or tc.get("name") not in self.blocked_tools
            ]

            # Update the message
            if len(filtered_calls) < len(tool_calls):
                blocked = [
                    tc.get("name")
                    for tc in tool_calls
                    if tc.get("name") in self.blocked_tools
                ]
                if blocked:
                    print(f"🥑 AvocadoDB exclusivity: Blocked {', '.join(blocked)}")

                # Modify the message in place
                last_message.tool_calls = filtered_calls

        return state
