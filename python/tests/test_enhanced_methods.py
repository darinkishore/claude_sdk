"""
Integration tests for enhanced Python binding methods.
This tests the current implementation and prepares for new methods.
"""
import os
import pytest
from pathlib import Path
import claude_sdk

# Use the fixture bundled with the Rust tests
FIXTURE_PATH = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "sessions"
    / "swe_fixer_download_debug.jsonl"
)


class TestCurrentMethods:
    """Test methods that are currently implemented"""
    
    def test_load_session(self):
        """Test basic session loading"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Basic assertions
        assert session is not None
        assert hasattr(session, 'session_id')
        assert hasattr(session, 'messages')
        assert hasattr(session, 'total_cost')
        assert hasattr(session, 'tools_used')
        assert hasattr(session, 'duration')
        
        # Check we have messages
        assert len(session.messages) > 0
        
        # Check message properties
        first_msg = session.messages[0]
        assert hasattr(first_msg, 'role')
        assert hasattr(first_msg, 'text')
        assert hasattr(first_msg, 'cost')
        assert hasattr(first_msg, 'tools')
        assert hasattr(first_msg, 'timestamp')
        assert hasattr(first_msg, 'uuid')
        assert hasattr(first_msg, 'parent_uuid')
        assert hasattr(first_msg, 'is_sidechain')
        assert hasattr(first_msg, 'cwd')
    
    def test_message_get_tool_blocks(self):
        """Test get_tool_blocks method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Find a message with tools
        tool_message = None
        for msg in session.messages:
            if msg.tools:
                tool_message = msg
                break
        
        if tool_message:
            tool_blocks = tool_message.get_tool_blocks()
            assert isinstance(tool_blocks, list)
            # Each tool block should have id, name, and input
            for block in tool_blocks:
                assert hasattr(block, 'id')
                assert hasattr(block, 'name')
                assert hasattr(block, 'input')
    
    def test_session_get_main_chain(self):
        """Test get_main_chain method"""
        session = claude_sdk.load(FIXTURE_PATH)
        main_chain = session.get_main_chain()
        
        assert isinstance(main_chain, list)
        # Main chain should exclude sidechains
        for msg in main_chain:
            assert not msg.is_sidechain
    
    def test_session_get_messages_by_role(self):
        """Test get_messages_by_role method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        user_messages = session.get_messages_by_role("user")
        assistant_messages = session.get_messages_by_role("assistant")
        
        assert isinstance(user_messages, list)
        assert isinstance(assistant_messages, list)
        
        # Check all messages have correct role
        for msg in user_messages:
            assert msg.role == "user"
        for msg in assistant_messages:
            assert msg.role == "assistant"


class TestEnhancedMethods:
    """Test methods that should be added from the dirty branch"""
    
    def test_message_get_text_blocks(self):
        """Test get_text_blocks method"""
        session = claude_sdk.load(FIXTURE_PATH)
        msg = session.messages[0]
        
        text_blocks = msg.get_text_blocks()
        assert isinstance(text_blocks, list)
        for block in text_blocks:
            assert hasattr(block, 'text')
            assert isinstance(block.text, str)
    
    def test_message_has_tool_use(self):
        """Test has_tool_use method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Find messages with and without tools
        has_tools = False
        no_tools = False
        
        for msg in session.messages:
            if msg.tools:
                assert msg.has_tool_use()
                has_tools = True
            else:
                assert not msg.has_tool_use()
                no_tools = True
        
        # Make sure we tested both cases
        assert has_tools and no_tools
    
    def test_message_token_properties(self):
        """Test token usage properties"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Find an assistant message (likely to have token info)
        for msg in session.messages:
            if msg.role == "assistant":
                # These properties should exist even if None
                assert hasattr(msg, 'total_tokens')
                assert hasattr(msg, 'input_tokens')
                assert hasattr(msg, 'output_tokens')
                assert hasattr(msg, 'stop_reason')
                assert hasattr(msg, 'model')
                break
    
    def test_session_get_messages_by_tool(self):
        """Test get_messages_by_tool method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Find a tool that's used
        if session.tools_used:
            tool_name = session.tools_used[0]
            tool_messages = session.get_messages_by_tool(tool_name)
            
            assert isinstance(tool_messages, list)
            for msg in tool_messages:
                assert tool_name in msg.tools
    
    def test_session_get_message_by_uuid(self):
        """Test get_message_by_uuid method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Get a known UUID
        target_uuid = session.messages[0].uuid
        found_msg = session.get_message_by_uuid(target_uuid)
        
        assert found_msg is not None
        assert found_msg.uuid == target_uuid
        
        # Test non-existent UUID
        not_found = session.get_message_by_uuid("non-existent-uuid")
        assert not_found is None
    
    def test_session_filter_messages(self):
        """Test filter_messages method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Filter for user messages
        user_msgs = session.filter_messages(lambda m: m.role == "user")
        assert all(m.role == "user" for m in user_msgs)
        
        # Filter for messages with cost > 0
        costly_msgs = session.filter_messages(lambda m: m.cost and m.cost > 0)
        assert all(m.cost and m.cost > 0 for m in costly_msgs)
    
    def test_session_get_thread(self):
        """Test get_thread method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Find a message with a parent
        for msg in session.messages:
            if msg.parent_uuid:
                thread = session.get_thread(msg.uuid)
                assert isinstance(thread, list)
                assert len(thread) >= 2  # At least the message and its parent
                assert thread[-1].uuid == msg.uuid
                # Verify parent-child relationships
                for i in range(1, len(thread)):
                    assert thread[i].parent_uuid == thread[i-1].uuid
                break
    
    @pytest.mark.skip(reason="Method not yet implemented")
    def test_session_calculate_metrics(self):
        """Test calculate_metrics method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        metrics = session.calculate_metrics()
        assert isinstance(metrics, dict)
        
        # Check expected metrics
        assert 'total_messages' in metrics
        assert 'user_messages' in metrics
        assert 'assistant_messages' in metrics
        assert 'total_cost' in metrics
        assert 'average_message_cost' in metrics
        assert 'unique_tools_used' in metrics
        assert 'total_tool_calls' in metrics
    
    @pytest.mark.skip(reason="Method not yet implemented")
    def test_session_to_dict(self):
        """Test to_dict method"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        session_dict = session.to_dict()
        assert isinstance(session_dict, dict)
        
        # Check key fields
        assert 'session_id' in session_dict
        assert 'total_cost' in session_dict
        assert 'tools_used' in session_dict
        assert 'messages' in session_dict
        
        # Messages should be dicts too
        assert isinstance(session_dict['messages'], list)
        if session_dict['messages']:
            assert isinstance(session_dict['messages'][0], dict)
    
    def test_session_iteration(self):
        """Test __len__ and __iter__ methods"""
        session = claude_sdk.load(FIXTURE_PATH)
        
        # Test length
        assert len(session) == len(session.messages)
        
        # Test iteration
        count = 0
        for msg in session:
            assert hasattr(msg, 'uuid')
            count += 1
        assert count == len(session.messages)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])