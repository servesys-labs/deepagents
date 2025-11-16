"""AvocadoDB integration for DeepAgents CLI.

AvocadoDB provides deterministic, citation-backed context retrieval for agents.
Unlike traditional RAG systems, AvocadoDB guarantees:
- 100% deterministic results (same query → same context, every time)
- Perfect citations (exact file:line references)
- 95%+ token efficiency (vs 60-70% with traditional RAG)
- Zero duplicate content

Auto-start: Set AVOCADODB_AUTO_START=true to automatically start server

Learn more: https://github.com/avocadodb/avocadodb
"""

import os
from typing import Any

from deepagents_cli.integrations.avocadodb_auto import ensure_running


def avocado_compile_context(
    query: str,
    token_budget: int = 8000,
    semantic_weight: float = 0.7,
    lexical_weight: float = 0.3,
    mmr_lambda: float = 0.5,
    enable_mmr: bool = True,
) -> dict[str, Any]:
    """Compile deterministic, citation-backed context from AvocadoDB knowledge base.

    AvocadoDB provides 100% deterministic context compilation - the same query
    always returns the same context, making your agent's responses reproducible
    and auditable. Every span includes exact line number citations.

    This tool searches your ingested codebase/documentation and returns relevant
    context that you MUST synthesize into a natural response for the user.

    Use this when you need to:
    - Retrieve information from ingested documentation or code
    - Get verifiable, citation-backed answers
    - Ensure consistent responses across multiple runs
    - Access knowledge with perfect reproducibility

    Args:
        query: Search query describing what information you need (be specific)
        token_budget: Maximum tokens to use (default: 8000)
        semantic_weight: Weight for semantic (vector) search 0.0-1.0 (default: 0.7)
        lexical_weight: Weight for lexical (keyword) search 0.0-1.0 (default: 0.3)
        mmr_lambda: Diversity parameter 0.0-1.0 (default: 0.5, higher = more diverse)
        enable_mmr: Enable Maximal Marginal Relevance diversification (default: True)

    Returns:
        Dictionary containing:
        - success: Whether the compilation succeeded
        - context: The compiled context text (use this in your response)
        - citations: List of citations with file paths and line numbers
        - spans: Number of spans included
        - tokens_used: Actual tokens used
        - compilation_time_ms: Compilation time in milliseconds
        - deterministic_hash: SHA-256 hash of context (same query = same hash)

    IMPORTANT: After using this tool:
    1. Read through the 'context' field - this contains the relevant information
    2. Extract what's needed to answer the user's question
    3. Synthesize this into a clear, natural language response
    4. Cite sources by mentioning file names and line numbers from 'citations'
    5. NEVER show the raw JSON to the user - always provide a formatted response

    Setup:
        With auto-start enabled (default), just run avacado-cli!

        Or manually:
        1. Start AvocadoDB server: ./target/release/avocado-server (port 8765)
        2. Ingest documents: ./target/release/avocado ingest ./docs --recursive
        3. Set AVOCADODB_URL (optional): export AVOCADODB_URL="http://localhost:8765"

    Example Response:
        "The authentication system uses JWT tokens (see auth.md:10-25). The token
        validation happens in the middleware layer (src/auth.ts:45-78)..."
    """
    # Auto-start server if configured
    ensure_running()

    try:
        import requests

        # Get server URL from environment or use default
        server_url = os.environ.get("AVOCADODB_URL", "http://localhost:8765")

        # Call AvocadoDB compile endpoint
        response = requests.post(
            f"{server_url}/compile",
            json={
                "query": query,
                "token_budget": token_budget,
                "semantic_weight": semantic_weight,
                "lexical_weight": lexical_weight,
                "mmr_lambda": mmr_lambda,
                "enable_mmr": enable_mmr,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"AvocadoDB API error: {response.status_code}",
                "context": "",
                "citations": [],
                "query": query,
                "hint": "Check if AvocadoDB server is running on port 8765",
            }

        data = response.json()

        # Format citations for easy reference
        formatted_citations = [
            {
                "file": citation["artifact_path"],
                "lines": f"{citation['start_line']}-{citation['end_line']}",
            }
            for citation in data.get("citations", [])
        ]

        # Calculate deterministic hash
        import hashlib

        context_text = data.get("text", "")
        det_hash = hashlib.sha256(context_text.encode("utf-8")).hexdigest()

        return {
            "success": True,
            "context": context_text,
            "citations": formatted_citations,
            "spans": len(data.get("spans", [])),
            "tokens_used": data.get("tokens_used", 0),
            "compilation_time_ms": data.get("compilation_time_ms", 0),
            "deterministic_hash": det_hash,
            "query": query,
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "AvocadoDB not available - falling back to other tools",
            "context": "",
            "citations": [],
            "query": query,
            "hint": (
                "💡 Want deterministic context retrieval? Install AvocadoDB:\n\n"
                "   Quick Install (copy-paste):\n"
                "   curl -fsSL https://raw.githubusercontent.com/avocadodb/avocadodb/main/install.sh | sh\n\n"
                "   Or manual install:\n"
                "   git clone https://github.com/avocadodb/avocadodb && cd avocadodb\n"
                "   cargo build --release && ./target/release/avocado-server &\n\n"
                "   Benefits: 100% deterministic, citation-backed, 95% token efficiency\n"
                "   Docs: https://github.com/avocadodb/avocadodb"
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AvocadoDB error: {str(e)}",
            "context": "",
            "citations": [],
            "query": query,
        }


__all__ = ["avocado_compile_context"]
