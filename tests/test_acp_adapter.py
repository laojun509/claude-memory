"""Tests for ACP adapter."""
import pytest
from unittest.mock import Mock, patch
from claude_memory.integrations.acp_adapter import ACPMemoryAdapter
from claude_memory.core.models import Memory, EntityType


@pytest.fixture
def adapter(tmp_path):
    """Create adapter with temp directory."""
    return ACPMemoryAdapter(project_id="test_project", persist_dir=str(tmp_path / "memory"))


def test_adapter_initialization(adapter):
    """Test adapter can be initialized."""
    assert adapter.project_id == "test_project"
    assert adapter.engine is not None


def test_on_conversation_end(adapter):
    """Test processing conversation end."""
    with patch.object(adapter.engine, 'process_conversation') as mock_process:
        mock_process.return_value = [
            Memory(content="提取的记忆", entity_type=EntityType.FACT),
        ]
        
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        
        result = adapter.on_conversation_end(conversation)
        
        assert len(result) == 1
        mock_process.assert_called_once_with(conversation, project_id="test_project")


def test_enhance_system_prompt(adapter):
    """Test enhancing system prompt with memories."""
    with patch.object(adapter.engine, 'get_enhanced_system_prompt') as mock_enhance:
        mock_enhance.return_value = "Enhanced prompt with memories"
        
        conversation = [{"role": "user", "content": "Hello"}]
        result = adapter.enhance_system_prompt("Base prompt", conversation)
        
        assert "Enhanced" in result
        mock_enhance.assert_called_once_with("Base prompt", conversation, project_id="test_project")


def test_get_memory_context(adapter):
    """Test getting memory context for conversation."""
    with patch.object(adapter.engine, 'get_context') as mock_get_context:
        mock_get_context.return_value = [
            Memory(content="上下文记忆", entity_type=EntityType.FACT),
        ]
        
        conversation = [{"role": "user", "content": "Help"}]
        result = adapter.get_memory_context(conversation, max_memories=3)
        
        assert len(result) == 1
        mock_get_context.assert_called_once_with(conversation, project_id="test_project", max_memories=3)


def test_search(adapter):
    """Test searching memories."""
    with patch.object(adapter.engine, 'search_memories') as mock_search:
        mock_search.return_value = [
            Memory(content="搜索结果", entity_type=EntityType.FACT),
        ]
        
        result = adapter.search("test query", limit=5)
        
        assert len(result) == 1
        mock_search.assert_called_once_with("test query", project_id="test_project", limit=5)


def test_add_manual_memory(adapter):
    """Test manually adding a memory."""
    with patch.object(adapter.engine.store, 'add', return_value="mem_123") as mock_add:
        result = adapter.add_manual_memory("手动记忆", memory_type="fact")
        
        assert result == "mem_123"
        mock_add.assert_called_once()
        # Verify memory was created with correct parameters
        call_args = mock_add.call_args[0][0]
        assert call_args.content == "手动记忆"
        assert call_args.entity_type == EntityType.FACT
        assert call_args.project_id == "test_project"
        assert call_args.importance == 0.7


def test_on_conversation_start(adapter):
    """Test conversation start handler."""
    # Should not raise any errors
    adapter.on_conversation_start("conv_123")
