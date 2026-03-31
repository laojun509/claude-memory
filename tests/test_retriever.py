"""Tests for smart memory retriever."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from claude_memory.retrievers.smart_retriever import SmartRetriever
from claude_memory.core.models import Memory, EntityType


@pytest.fixture
def mock_store():
    """Create mock memory store."""
    store = Mock()
    return store


@pytest.fixture
def retriever(mock_store):
    """Create retriever with mock store."""
    return SmartRetriever(mock_store)


def test_retrieve_relevant_memories(retriever, mock_store):
    """Test retrieving relevant memories for a query."""
    mock_store.search.return_value = [
        Memory(content="用户讨厌前端", entity_type=EntityType.PREFERENCE, importance=0.8, project_id="proj_1"),
        Memory(content="项目用 FastAPI", entity_type=EntityType.PROJECT, importance=0.7, project_id="proj_1"),
    ]
    
    results = retriever.retrieve("我应该用什么框架做后端？", project_id="proj_1")
    
    assert len(results) > 0
    mock_store.search.assert_called_once()


def test_rank_by_importance(retriever, mock_store):
    """Test that high-importance memories are ranked higher."""
    high_importance = Memory(
        content="核心架构决策", 
        entity_type=EntityType.DECISION, 
        importance=0.95, 
        project_id="proj_1"
    )
    low_importance = Memory(
        content="minor detail", 
        entity_type=EntityType.FACT, 
        importance=0.3, 
        project_id="proj_1"
    )
    
    mock_store.search.return_value = [low_importance, high_importance]
    
    results = retriever.retrieve("架构相关", project_id="proj_1")
    
    # High importance should come first
    assert results[0].importance > results[1].importance
    assert results[0].content == "核心架构决策"


def test_filter_by_entity_type(retriever, mock_store):
    """Test filtering by entity type."""
    mock_store.search.return_value = [
        Memory(content="喜欢 Python", entity_type=EntityType.PREFERENCE, importance=0.8),
        Memory(content="用 FastAPI", entity_type=EntityType.PROJECT, importance=0.7),
        Memory(content="代码规范", entity_type=EntityType.CODE_STYLE, importance=0.6),
    ]
    
    results = retriever.retrieve("test", entity_types=[EntityType.PREFERENCE, EntityType.PROJECT])
    
    assert len(results) == 2
    assert all(r.entity_type in [EntityType.PREFERENCE, EntityType.PROJECT] for r in results)


def test_get_context_for_conversation(retriever, mock_store):
    """Test getting context for conversation."""
    mock_store.search.return_value = [
        Memory(content="之前的记忆", entity_type=EntityType.FACT, importance=0.7),
    ]
    
    conversation = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "新问题"},
        {"role": "assistant", "content": "回答"},
    ]
    
    results = retriever.get_context_for_conversation(conversation, project_id="test")
    
    assert len(results) == 1
    mock_store.search.assert_called_once()


def test_get_context_empty_conversation(retriever):
    """Test context with empty conversation."""
    results = retriever.get_context_for_conversation([])
    assert len(results) == 0


def test_get_context_no_user_message(retriever, mock_store):
    """Test context with no user message."""
    conversation = [
        {"role": "system", "content": "System prompt"},
        {"role": "assistant", "content": "Hello"},
    ]
    
    results = retriever.get_context_for_conversation(conversation)
    assert len(results) == 0


def test_relevance_score_calculation(retriever):
    """Test relevance score calculation."""
    memory = Memory(
        content="test",
        entity_type=EntityType.DECISION,
        importance=0.9,
        timestamp=datetime.now(),
    )
    
    score = retriever._calculate_relevance_score(memory, "test query")
    
    # Should be high due to importance, recency, and decision type
    assert score > 0.5
    assert score <= 1.0


def test_relevance_score_with_old_memory(retriever):
    """Test score for old memory."""
    old_memory = Memory(
        content="test",
        entity_type=EntityType.FACT,
        importance=0.5,
        timestamp=datetime.now() - timedelta(days=10),
    )
    
    score = retriever._calculate_relevance_score(old_memory, "test")
    
    # Should be lower due to age
    assert score < 0.6
