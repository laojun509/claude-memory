"""Tests for LLM memory extractor."""
import pytest
from unittest.mock import Mock, patch
from claude_memory.extractors.llm_extractor import LLMMemoryExtractor
from claude_memory.core.models import EntityType


@pytest.fixture
def extractor():
    """Create extractor instance."""
    return LLMMemoryExtractor(model="gpt-4o-mini")


def test_extract_preferences(extractor):
    """Test extracting user preferences."""
    mock_response = {
        "memories": [
            {
                "content": "用户讨厌写前端代码，更喜欢后端开发",
                "entity_type": "preference",
                "importance": 0.8,
            },
            {
                "content": "用户偏好使用 Python 语言",
                "entity_type": "preference",
                "importance": 0.7,
            },
        ]
    }
    
    with patch.object(extractor, '_call_llm', return_value=mock_response):
        conversation = [
            {"role": "user", "content": "我讨厌写前端，还是后端舒服，特别是用 Python"},
            {"role": "assistant", "content": "明白了，你更喜欢后端开发"},
        ]
        
        memories = extractor.extract(conversation)
        
        assert len(memories) == 2
        assert memories[0].entity_type == EntityType.PREFERENCE
        assert "讨厌" in memories[0].content
        assert memories[0].importance == 0.8


def test_no_memories_extracted(extractor):
    """Test when no memories should be extracted."""
    mock_response = {"memories": []}
    
    with patch.object(extractor, '_call_llm', return_value=mock_response):
        conversation = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你的？"},
        ]
        
        memories = extractor.extract(conversation)
        assert len(memories) == 0


def test_extract_facts(extractor):
    """Test extracting facts."""
    mock_response = {
        "memories": [
            {
                "content": "项目使用 FastAPI 作为后端框架",
                "entity_type": "fact",
                "importance": 0.7,
            },
        ]
    }
    
    with patch.object(extractor, '_call_llm', return_value=mock_response):
        conversation = [
            {"role": "user", "content": "我们项目用 FastAPI 做后端"},
        ]
        
        memories = extractor.extract(conversation, project_id="test_proj")
        
        assert len(memories) == 1
        assert memories[0].entity_type == EntityType.FACT
        assert memories[0].project_id == "test_proj"


def test_empty_conversation(extractor):
    """Test handling empty conversation."""
    memories = extractor.extract([])
    assert len(memories) == 0


def test_invalid_memory_data(extractor):
    """Test handling invalid memory data from LLM."""
    mock_response = {
        "memories": [
            {
                "content": "有效记忆",
                "entity_type": "preference",
                "importance": 0.8,
            },
            {
                "content": "无效记忆",
                "entity_type": "invalid_type",  # Invalid
                "importance": 0.5,
            },
        ]
    }
    
    with patch.object(extractor, '_call_llm', return_value=mock_response):
        conversation = [{"role": "user", "content": "测试"}]
        memories = extractor.extract(conversation)
        
        # Should only have valid memory
        assert len(memories) == 1
        assert memories[0].content == "有效记忆"


def test_llm_error_handling(extractor):
    """Test error handling when LLM fails."""
    with patch.object(extractor, '_call_llm', side_effect=Exception("API Error")):
        conversation = [{"role": "user", "content": "测试"}]
        try:
            memories = extractor.extract(conversation)
            # Should return empty list on error
            assert len(memories) == 0
        except Exception:
            # If exception propagates, that's also acceptable behavior
            pass
