"""Tests for core memory engine."""
import pytest
from unittest.mock import Mock, patch
from claude_memory.core.engine import MemoryEngine
from claude_memory.core.models import Memory, EntityType


@pytest.fixture
def temp_engine(tmp_path):
    """Create temporary engine."""
    return MemoryEngine(persist_dir=str(tmp_path / "memory_db"))


def test_process_conversation_extraction(temp_engine):
    """Test processing conversation extracts memories."""
    with patch.object(temp_engine.extractor, 'extract') as mock_extract:
        mock_extract.return_value = [
            Memory(content="测试记忆", entity_type=EntityType.FACT, importance=0.7, project_id="test"),
        ]
        
        conversation = [
            {"role": "user", "content": "测试对话"},
            {"role": "assistant", "content": "测试回复"},
        ]
        
        temp_engine.process_conversation(conversation, project_id="test")
        
        mock_extract.assert_called_once()


def test_get_context_for_new_conversation(temp_engine):
    """Test getting context for new conversation."""
    with patch.object(temp_engine.retriever, 'get_context_for_conversation') as mock_retrieve:
        mock_retrieve.return_value = [
            Memory(content="之前的记忆", entity_type=EntityType.FACT, importance=0.7, project_id="test"),
        ]
        
        conversation = [{"role": "user", "content": "新问题"}]
        context = temp_engine.get_context(conversation, project_id="test")
        
        assert len(context) == 1
        assert "之前的记忆" in context[0].content


def test_get_enhanced_system_prompt_with_memories(temp_engine):
    """Test enhancing system prompt with memories."""
    with patch.object(temp_engine.retriever, 'get_context_for_conversation') as mock_get_context:
        mock_get_context.return_value = [
            Memory(content="用户喜欢 Python", entity_type=EntityType.PREFERENCE, importance=0.8),
        ]
        
        with patch.object(temp_engine.injector, 'should_inject', return_value=True):
            conversation = [{"role": "user", "content": "Help me"}]
            prompt = temp_engine.get_enhanced_system_prompt(
                "You are helpful.",
                conversation,
            )
            
            assert "用户喜欢 Python" in prompt
            assert "RELEVANT CONTEXT" in prompt


def test_get_enhanced_system_prompt_no_injection(temp_engine):
    """Test system prompt without injection."""
    with patch.object(temp_engine.retriever, 'get_context_for_conversation') as mock_get_context:
        mock_get_context.return_value = []
        
        conversation = [{"role": "user", "content": "Hello"}]
        base_prompt = "You are helpful."
        prompt = temp_engine.get_enhanced_system_prompt(base_prompt, conversation)
        
        assert prompt == base_prompt


def test_search_memories(temp_engine):
    """Test searching memories."""
    with patch.object(temp_engine.store, 'search') as mock_search:
        mock_search.return_value = [
            Memory(content="Python 相关内容", entity_type=EntityType.FACT),
        ]
        
        results = temp_engine.search_memories("Python", project_id="test")
        
        assert len(results) == 1
        mock_search.assert_called_once_with("Python", limit=5, project_id="test")


def test_get_project_memories(temp_engine):
    """Test getting all memories for a project."""
    with patch.object(temp_engine.store, 'get_by_project') as mock_get:
        mock_get.return_value = [
            Memory(content="记忆1", project_id="proj_1"),
            Memory(content="记忆2", project_id="proj_1"),
        ]
        
        memories = temp_engine.get_project_memories("proj_1")
        
        assert len(memories) == 2
        mock_get.assert_called_once_with("proj_1")


def test_delete_memory(temp_engine):
    """Test deleting a memory."""
    with patch.object(temp_engine.store, 'delete', return_value=True) as mock_delete:
        result = temp_engine.delete_memory("mem_123")
        
        assert result is True
        mock_delete.assert_called_once_with("mem_123")
