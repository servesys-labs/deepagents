"""AvocadoDB integration for DeepAgents CLI.

Now using the AvocadoDB SDK for framework-agnostic functionality.
All features (auto-start, monitoring, ingestion) come from the SDK.

Learn more: https://github.com/avocadodb/avocadodb
"""

# Import directly from AvocadoDB SDK
from avocado.integrations.langchain import avocado_compile_context

# For backward compatibility, also import manager functions
from avocado.manager import get_manager, AvocadoDBManager


def ensure_running() -> bool:
    """Ensure AvocadoDB server is running (SDK wrapper for compatibility).

    Returns:
        True if server is available
    """
    manager = get_manager()
    return manager.ensure_running()


def get_stats() -> dict:
    """Get database statistics (SDK wrapper for compatibility).

    Returns:
        Dict with stats like artifacts_count, spans_count, total_tokens
    """
    manager = get_manager()
    return manager.get_stats()


def get_startup_info() -> str:
    """Get startup information for AvocadoDB (SDK wrapper for compatibility).

    Returns:
        Formatted string with server status and indexing stats
    """
    manager = get_manager()

    # Ensure server is running (will auto-start if needed)
    is_running = manager.ensure_running()

    if not is_running:
        return "  [dim]🥑 AvocadoDB: Not available[/dim]"

    # Get stats
    stats = manager.get_stats()

    if not stats:
        return "  [dim]🥑 AvocadoDB: Server running (no stats available)[/dim]"

    # Extract useful stats
    artifacts_count = stats.get("artifacts_count", 0)
    spans_count = stats.get("spans_count", 0)
    total_tokens = stats.get("total_tokens", 0)

    # Format the message
    if artifacts_count > 0:
        return f"  [green]🥑 AvocadoDB: Ready[/green] [dim]({artifacts_count} docs, {spans_count} spans, {total_tokens:,} tokens)[/dim]"
    else:
        return "  [yellow]🥑 AvocadoDB: Ready[/yellow] [dim](no items indexed yet - will auto-ingest on first query)[/dim]"


__all__ = ["avocado_compile_context", "ensure_running", "get_stats", "get_startup_info"]
