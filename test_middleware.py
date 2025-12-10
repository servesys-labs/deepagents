"""Test script to verify AvocadoDB exclusivity middleware works correctly."""

from langchain.agents.middleware.types import ModelResponse
from langchain_core.messages import AIMessage, ToolCall
from deepagents_cli.avocado_middleware import AvocadoDBExclusivityMiddleware


def test_middleware_filters_parallel_tools():
    """Test that middleware filters read tools when avocado is called in parallel."""

    # Create middleware
    middleware = AvocadoDBExclusivityMiddleware()

    # Create a mock AI message with parallel tool calls (avocado + read_file + grep)
    tool_calls = [
        {"name": "avocado_compile_context", "args": {"query": "test"}, "id": "call_1"},
        {"name": "read_file", "args": {"file_path": "/test.py"}, "id": "call_2"},
        {"name": "grep", "args": {"pattern": "test"}, "id": "call_3"},
        {"name": "ls", "args": {"path": "/"}, "id": "call_4"},
    ]

    ai_message = AIMessage(content="", tool_calls=tool_calls)

    # Create a mock ModelResponse
    response = ModelResponse(result=[ai_message])

    print("Before middleware:")
    print(f"  Tool calls: {[tc['name'] for tc in ai_message.tool_calls]}")

    # Run middleware
    filtered_response = middleware.after_model(response, runtime=None)

    print("\nAfter middleware:")
    if filtered_response:
        filtered_calls = filtered_response.result[-1].tool_calls
        print(f"  Tool calls: {[tc['name'] for tc in filtered_calls]}")
        print(f"  ✅ Filtered {len(tool_calls) - len(filtered_calls)} tools")

        # Verify only avocado_compile_context remains
        assert len(filtered_calls) == 1
        assert filtered_calls[0]["name"] == "avocado_compile_context"
        print("  ✅ Only avocado_compile_context remains!")
    else:
        print("  ❌ No filtering occurred")
        return False

    return True


def test_middleware_allows_non_conflicting_tools():
    """Test that middleware allows other tools when avocado is called alongside them."""

    middleware = AvocadoDBExclusivityMiddleware()

    # Create tool calls with avocado + non-conflicting tool (write_file)
    tool_calls = [
        {"name": "avocado_compile_context", "args": {"query": "test"}, "id": "call_1"},
        {"name": "write_file", "args": {"file_path": "/test.py", "content": "test"}, "id": "call_2"},
    ]

    ai_message = AIMessage(content="", tool_calls=tool_calls)
    response = ModelResponse(result=[ai_message])

    print("\nTesting non-conflicting tools:")
    print(f"  Before: {[tc['name'] for tc in ai_message.tool_calls]}")

    filtered_response = middleware.after_model(response, runtime=None)

    if filtered_response:
        filtered_calls = filtered_response.result[-1].tool_calls
        print(f"  After: {[tc['name'] for tc in filtered_calls]}")
        # Both should remain since write_file is not blocked
        assert len(filtered_calls) == 2
        print("  ✅ Non-conflicting tools preserved!")
    else:
        # None means no changes needed - both tools are fine
        print("  ✅ No filtering needed - all tools allowed!")

    return True


def test_middleware_ignores_non_avocado_calls():
    """Test that middleware doesn't interfere when avocado is not called."""

    middleware = AvocadoDBExclusivityMiddleware()

    # Create tool calls WITHOUT avocado
    tool_calls = [
        {"name": "read_file", "args": {"file_path": "/test.py"}, "id": "call_1"},
        {"name": "grep", "args": {"pattern": "test"}, "id": "call_2"},
    ]

    ai_message = AIMessage(content="", tool_calls=tool_calls)
    response = ModelResponse(result=[ai_message])

    print("\nTesting without avocado:")
    print(f"  Tool calls: {[tc['name'] for tc in ai_message.tool_calls]}")

    filtered_response = middleware.after_model(response, runtime=None)

    if filtered_response is None:
        print("  ✅ Middleware correctly ignores non-avocado calls!")
        return True
    else:
        print("  ❌ Middleware incorrectly filtered non-avocado calls")
        return False


def test_middleware_with_dict_format():
    """Test that middleware works with dict format (actual runtime format)."""

    middleware = AvocadoDBExclusivityMiddleware()

    # Create tool calls in dict format (as used in actual runtime)
    tool_calls = [
        {"name": "avocado_compile_context", "args": {"query": "test"}, "id": "call_1"},
        {"name": "read_file", "args": {"file_path": "/test.py"}, "id": "call_2"},
        {"name": "ls", "args": {"path": "/"}, "id": "call_3"},
    ]

    ai_message = AIMessage(content="", tool_calls=tool_calls)

    # Create response as a dict (actual LangGraph runtime format)
    response_dict = {"messages": [ai_message], "agent_memory": {}, "shell_session_resources": {}}

    print("\nTesting dict format (runtime format):")
    print(f"  Before: {[tc['name'] for tc in ai_message.tool_calls]}")

    # Run middleware with dict format
    filtered_response = middleware.after_model(response_dict, runtime=None)

    if filtered_response:
        # LangGraph uses "messages" key
        filtered_calls = filtered_response["messages"][-1].tool_calls
        print(f"  After: {[tc['name'] for tc in filtered_calls]}")
        assert len(filtered_calls) == 1
        assert filtered_calls[0]["name"] == "avocado_compile_context"
        print("  ✅ Dict format handled correctly!")
        return True
    else:
        print("  ❌ No filtering occurred with dict format")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing AvocadoDB Exclusivity Middleware")
    print("=" * 60)

    try:
        # Run all tests
        test1 = test_middleware_filters_parallel_tools()
        test2 = test_middleware_allows_non_conflicting_tools()
        test3 = test_middleware_ignores_non_avocado_calls()
        test4 = test_middleware_with_dict_format()

        print("\n" + "=" * 60)
        if all([test1, test2, test3, test4]):
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
