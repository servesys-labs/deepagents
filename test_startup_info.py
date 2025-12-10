"""Test script to show AvocadoDB startup info."""

from deepagents_cli.integrations.avocadodb_auto import get_startup_info, get_stats
from rich.console import Console

console = Console()

print("=" * 60)
print("AvocadoDB Startup Info Test")
print("=" * 60)

# Get stats
stats = get_stats()
print(f"\nRaw stats from server: {stats}")

# Get formatted startup info
startup_info = get_startup_info()
print(f"\nFormatted startup message:")
console.print(startup_info)

print("\n" + "=" * 60)
print("This is what you'll see when starting the CLI!")
print("=" * 60)
