"""Middleware to enforce AvocadoDB exclusivity.

Now using the AvocadoDB SDK middleware instead of custom implementation.
"""

# Import directly from AvocadoDB SDK
from avocado.integrations.langchain import AvocadoDBMiddleware as _AvocadoDBMiddleware


# Re-export for compatibility
class AvocadoDBExclusivityMiddleware(_AvocadoDBMiddleware):
    """Middleware that enforces AvocadoDB-only execution for codebase queries.

    Imported from AvocadoDB SDK - all logic is in the SDK now.

    When avocado_compile_context is called, blocks these tools:
    - read_file
    - grep
    - ls
    - glob

    This prevents the agent from calling multiple tools in parallel or sequentially,
    ensuring AvocadoDB is used exclusively for codebase questions.
    """
    pass


__all__ = ["AvocadoDBExclusivityMiddleware"]
