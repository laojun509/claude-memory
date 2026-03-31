import pytest
from datetime import datetime
from claude_memory.core.models import Memory, Relation, EntityType


def test_memory_creation():
    memory = Memory(
        id="mem_001",
        content="用户讨厌写前端代码",
        entity_type=EntityType.PREFERENCE,
        project_id="proj_001",
        importance=0.8,
    )
    assert memory.id == "mem_001"
    assert memory.entity_type == EntityType.PREFERENCE
    assert isinstance(memory.timestamp, datetime)


def test_relation_creation():
    rel = Relation(
        target_memory_id="mem_002",
        relation_type="contradicts",
        confidence=0.9,
    )
    assert rel.target_memory_id == "mem_002"
