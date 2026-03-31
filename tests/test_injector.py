"""Tests for prompt injector."""
import pytest
from claude_memory.injectors.prompt_injector import PromptInjector
from claude_memory.core.models import Memory, EntityType


@pytest.fixture
def injector():
    """Create injector instance."""
    return PromptInjector()


def test_format_memories_for_prompt(injector):
    """Test formatting memories for prompt injection."""
    memories = [
        Memory(content="用户讨厌前端开发", entity_type=EntityType.PREFERENCE, importance=0.8, project_id="proj_1"),
        Memory(content="项目使用 FastAPI", entity_type=EntityType.PROJECT, importance=0.7, project_id="proj_1"),
    ]
    
    prompt = injector.format_memories(memories)
    
    assert "用户讨厌前端开发" in prompt
    assert "项目使用 FastAPI" in prompt
    assert "RELEVANT CONTEXT" in prompt
    assert "💭" in prompt  # Preference emoji
    assert "📁" in prompt  # Project emoji


def test_empty_memories(injector):
    """Test with no memories."""
    prompt = injector.format_memories([])
    assert prompt == ""


def test_create_system_prompt(injector):
    """Test creating full system prompt with memories."""
    base_prompt = "You are a helpful coding assistant."
    memories = [
        Memory(content="用户偏好 Python", entity_type=EntityType.PREFERENCE, importance=0.8, project_id="proj_1"),
    ]
    
    full_prompt = injector.create_system_prompt(base_prompt, memories)
    
    assert base_prompt in full_prompt
    assert "用户偏好 Python" in full_prompt
    assert "RELEVANT CONTEXT" in full_prompt


def test_create_system_prompt_no_memories(injector):
    """Test creating prompt without memories."""
    base_prompt = "You are helpful."
    
    full_prompt = injector.create_system_prompt(base_prompt, [])
    
    assert full_prompt == base_prompt


def test_should_inject_with_high_importance(injector):
    """Test injection decision with high importance memory."""
    memories = [
        Memory(content="重要记忆", entity_type=EntityType.DECISION, importance=0.9),
    ]
    conversation = [{"role": "user", "content": "Hello"}]
    
    should = injector.should_inject(conversation, memories)
    assert should is True


def test_should_not_inject_empty_memories(injector):
    """Test no injection with empty memories."""
    conversation = [{"role": "user", "content": "Hello"}]
    
    should = injector.should_inject(conversation, [])
    assert should is False


def test_should_inject_with_trigger_words(injector):
    """Test injection with trigger words in conversation."""
    memories = [
        Memory(content="记忆", entity_type=EntityType.FACT, importance=0.6),
    ]
    conversation = [{"role": "user", "content": "Remember what I said about Python?"}]
    
    should = injector.should_inject(conversation, memories)
    assert should is True


def test_should_inject_with_chinese_trigger(injector):
    """Test injection with Chinese trigger words."""
    memories = [
        Memory(content="记忆", entity_type=EntityType.FACT, importance=0.6),
    ]
    conversation = [{"role": "user", "content": "上次我们说过这个"}]
    
    should = injector.should_inject(conversation, memories)
    assert should is True


def test_should_not_inject_low_relevance(injector):
    """Test no injection with low relevance memories."""
    memories = [
        Memory(content="minor", entity_type=EntityType.FACT, importance=0.3),
        Memory(content="detail", entity_type=EntityType.FACT, importance=0.4),
    ]
    conversation = [{"role": "user", "content": "Hello there"}]
    
    should = injector.should_inject(conversation, memories, threshold=0.6)
    assert should is False


def test_get_prefix_for_type(injector):
    """Test emoji prefix mapping."""
    assert injector._get_prefix_for_type(EntityType.PREFERENCE) == "💭"
    assert injector._get_prefix_for_type(EntityType.FACT) == "📌"
    assert injector._get_prefix_for_type(EntityType.PROJECT) == "📁"
    assert injector._get_prefix_for_type(EntityType.CODE_STYLE) == "💻"
    assert injector._get_prefix_for_type(EntityType.DECISION) == "✅"
    assert injector._get_prefix_for_type(EntityType.TASK) == "📋"
