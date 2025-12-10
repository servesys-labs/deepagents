"""Test to compare token usage: AvocadoDB vs Traditional Tools.

This script will:
1. Ask the same question using AvocadoDB
2. Ask the same question using traditional tools (read_file, ls, grep)
3. Compare actual token usage
"""

import os
import sys

# Test query - realistic codebase question
TEST_QUERY = "How does the AvocadoDB compiler work? Explain the main components and algorithm."

print("=" * 80)
print("TOKEN USAGE COMPARISON TEST")
print("=" * 80)
print(f"\nTest Query: {TEST_QUERY}\n")
print("=" * 80)

print("\n📋 TEST SETUP:")
print("\nTest A: WITH AvocadoDB (current setup)")
print("  - Uses avocado_compile_context tool")
print("  - Middleware blocks traditional tools")
print("  - Should use ~3,000-5,000 tokens")

print("\nTest B: WITHOUT AvocadoDB (traditional tools)")
print("  - Middleware disabled")
print("  - Agent uses read_file, grep, ls")
print("  - Predicted: ~10,000-20,000 tokens")

print("\n" + "=" * 80)
print("MANUAL TEST INSTRUCTIONS:")
print("=" * 80)

print("""
Step 1: Test WITH AvocadoDB (current setup)
--------------------------------------------
Run in CLI:
  > How does the AvocadoDB compiler work? Explain the main components and algorithm.

Watch for:
  📊 AvocadoDB: X tokens used (budget: Y) | Z spans | Nms

Record the token count!


Step 2: Test WITHOUT AvocadoDB (disable middleware)
----------------------------------------------------
1. Edit avocado_middleware.py:
   Comment out line 142 (the print statement that blocks)

2. Edit agent.py:
   Comment out the AVOCADODB-ONLY PROTOCOL section (lines 132-152)

3. Restart CLI and run same query:
   > How does the AvocadoDB compiler work? Explain the main components and algorithm.

4. Count tokens from all tool calls:
   - Each read_file call shows lines read
   - Estimate: ~10-12 tokens per line
   - Add up all the reads

5. Compare the totals!


Alternative: Automated Test (WIP)
----------------------------------
We could automate this by:
1. Calling the agent with different configurations
2. Parsing tool call responses
3. Counting tokens automatically

But manual test is more transparent for now.
""")

print("\n" + "=" * 80)
print("Ready to test? Follow the steps above!")
print("=" * 80)
