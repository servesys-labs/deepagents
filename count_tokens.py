#!/usr/bin/env python3
"""Exact token counter for comparing AvocadoDB vs traditional tools.

Uses tiktoken for GPT models or approximation for Claude.
"""

import sys
import tiktoken

def count_tokens_exact(text: str, model: str = "gpt-4") -> int:
    """Count exact tokens using tiktoken.

    Args:
        text: Text to count tokens for
        model: Model to use for tokenization (gpt-4, gpt-3.5-turbo, etc.)

    Returns:
        Exact token count
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to cl100k_base (GPT-4 tokenizer)
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))


def count_tokens_from_file(filepath: str, num_lines: int = None) -> int:
    """Count tokens from a file.

    Args:
        filepath: Path to file
        num_lines: Number of lines to count (if limited read)

    Returns:
        Exact token count
    """
    with open(filepath, 'r') as f:
        if num_lines:
            lines = [f.readline() for _ in range(num_lines)]
            text = ''.join(lines)
        else:
            text = f.read()

    return count_tokens_exact(text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_tokens.py <filepath> [num_lines]")
        print("\nExample:")
        print("  python count_tokens.py docs/deepagents-integration.md 342")
        sys.exit(1)

    filepath = sys.argv[1]
    num_lines = int(sys.argv[2]) if len(sys.argv) > 2 else None

    tokens = count_tokens_from_file(filepath, num_lines)

    print(f"\n📊 Token Count (Exact):")
    print(f"  File: {filepath}")
    if num_lines:
        print(f"  Lines: {num_lines}")
    print(f"  Tokens: {tokens:,}")
    print()
