"""Middleware to enforce AvocadoDB exclusivity.

When the agent calls avocado_compile_context, this middleware blocks
all other read-oriented tools (read_file, grep, ls) from running in parallel.

This ensures deterministic, AvocadoDB-first behavior.
"""

from typing import Any

from langchain_core.runnables import RunnableConfig


class AvocadoDBExclusivityMiddleware:
    """Middleware that enforces AvocadoDB-only execution for codebase queries.

    When avocado_compile_context is called, blocks these tools:
    - read_file
    - grep
    - ls
    - glob

    This prevents the agent from calling multiple tools in parallel,
    ensuring AvocadoDB is used exclusively for codebase questions.
    """

    def __init__(self):
        """Initialize middleware."""
        # Tools to block when avocado_compile_context is active
        self.blocked_tools = {"read_file", "grep", "ls", "glob"}

    async def __call__(
        self,
        state: dict[str, Any],
        config: RunnableConfig,
        *,
        store: Any,
    ) -> dict[str, Any]:
        """Filter tool calls to enforce AvocadoDB exclusivity.

        If avocado_compile_context is being called, remove all read-oriented
        filesystem tools from the same turn.
        """
        messages = state.get("messages", [])

        if not messages:
            return state

        last_message = messages[-1]

        # Check if this is an AI message with tool calls
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state

        tool_calls = last_message.tool_calls

        # Check if avocado_compile_context is being called
        has_avocado = any(
            tc.get("name") == "avocado_compile_context"
            for tc in tool_calls
        )

        if has_avocado:
            # Filter out blocked tools, keep only avocado_compile_context
            filtered_calls = [
                tc for tc in tool_calls
                if tc.get("name") == "avocado_compile_context"
                or tc.get("name") not in self.blocked_tools
            ]

            # Update the message with filtered tool calls
            if len(filtered_calls) < len(tool_calls):
                last_message.tool_calls = filtered_calls

                # Log what we blocked
                blocked = [
                    tc.get("name")
                    for tc in tool_calls
                    if tc.get("name") in self.blocked_tools
                ]
                if blocked:
                    print(f"🥑 AvocadoDB exclusivity: Blocked parallel tools: {', '.join(blocked)}")

        return state
