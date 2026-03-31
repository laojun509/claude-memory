"""Tests for MemoryStore."""
import os
import shutil
import tempfile
from datetime import datetime

import pytest

from claude_memory.core.models import EntityType, Memory, Relation
from claude_memory.core.store import MemoryStore


@pytest.fixture
def temp_store():
    """Create a temporary memory store for testing."""
    temp_dir = tempfile.mkdtemp()
    store = MemoryStore(persist_dir=temp_dir)
    yield store
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    return Memory(
        id="mem_test_001",
        content="This is a test memory about Python programming",
        entity_type=EntityType.CODE_STYLE,
        source="test",
        project_id="test_project",
        importance=0.8
    )


@pytest.fixture
def sample_memories():
    """Create multiple sample memories for testing."""
    return [
        Memory(
            id="mem_python_001",
            content="Python is a high-level programming language with clean syntax",
            entity_type=EntityType.FACT,
            source="test",
            project_id="python_project",
            importance=0.7
        ),
        Memory(
            id="mem_python_002",
            content="Django is a Python web framework that follows MTV pattern",
            entity_type=EntityType.FACT,
            source="test",
            project_id="python_project",
            importance=0.6
        ),
        Memory(
            id="mem_js_001",
            content="JavaScript is used for web development and runs in browsers",
            entity_type=EntityType.FACT,
            source="test",
            project_id="js_project",
            importance=0.7
        ),
        Memory(
            id="mem_pref_001",
            content="User prefers dark mode interface for all applications",
            entity_type=EntityType.PREFERENCE,
            source="test",
            project_id="python_project",
            importance=0.9
        ),
    ]


def test_add_memory(temp_store, sample_memory):
    """Test adding a memory to the store."""
    # Add memory
    memory_id = temp_store.add(sample_memory)
    
    # Verify memory_id is returned
    assert memory_id == sample_memory.id
    
    # Verify memory can be found via search
    results = temp_store.search("Python programming", limit=5)
    assert len(results) >= 1
    
    # Check the content matches
    found = False
    for mem in results:
        if mem.id == sample_memory.id:
            found = True
            assert mem.content == sample_memory.content
            assert mem.entity_type == sample_memory.entity_type
            assert mem.project_id == sample_memory.project_id
            break
    assert found, "Added memory not found in search results"


def test_search_memory(temp_store, sample_memories):
    """Test semantic search functionality."""
    # Add multiple memories
    for memory in sample_memories:
        temp_store.add(memory)
    
    # Search for Python-related content
    results = temp_store.search("Python programming language", limit=3)
    
    # Should return relevant results
    assert len(results) > 0
    
    # The most relevant should be Python-related
    python_results = [r for r in results if "Python" in r.content]
    assert len(python_results) >= 1
    
    # Search for web development
    results = temp_store.search("web development browser", limit=2)
    assert len(results) > 0
    
    # Should include JavaScript-related memory
    js_results = [r for r in results if "JavaScript" in r.content or "browser" in r.content]
    assert len(js_results) >= 1


def test_search_with_project_filter(temp_store, sample_memories):
    """Test semantic search with project_id filter."""
    # Add multiple memories from different projects
    for memory in sample_memories:
        temp_store.add(memory)
    
    # Search without filter - should get results from all projects
    results_all = temp_store.search("programming", limit=10)
    assert len(results_all) >= 3  # Should have at least Python and JS results
    
    # Search with python_project filter
    results_python = temp_store.search("programming", limit=10, project_id="python_project")
    
    # All results should be from python_project
    assert len(results_python) >= 2
    for mem in results_python:
        assert mem.project_id == "python_project"
    
    # Should not include JavaScript memory
    js_in_results = any("JavaScript" in r.content for r in results_python)
    assert not js_in_results, "JS memory should not appear when filtering by python_project"


def test_get_by_project(temp_store, sample_memories):
    """Test getting all memories by project_id."""
    # Add multiple memories from different projects
    for memory in sample_memories:
        temp_store.add(memory)
    
    # Get memories for python_project
    python_memories = temp_store.get_by_project("python_project")
    
    # Should return all 3 python_project memories
    assert len(python_memories) == 3
    
    # All should have correct project_id
    for mem in python_memories:
        assert mem.project_id == "python_project"
    
    # Check specific memories are present
    memory_ids = {m.id for m in python_memories}
    assert "mem_python_001" in memory_ids
    assert "mem_python_002" in memory_ids
    assert "mem_pref_001" in memory_ids
    
    # Get memories for js_project
    js_memories = temp_store.get_by_project("js_project")
    
    # Should return only 1 js_project memory
    assert len(js_memories) == 1
    assert js_memories[0].id == "mem_js_001"
    
    # Get memories for non-existent project
    empty_memories = temp_store.get_by_project("non_existent_project")
    assert len(empty_memories) == 0


def test_delete_memory(temp_store, sample_memory):
    """Test deleting a memory from the store."""
    # Add memory
    temp_store.add(sample_memory)
    
    # Verify it exists
    results = temp_store.search(sample_memory.content, limit=1)
    assert len(results) > 0
    
    # Delete the memory
    deleted = temp_store.delete(sample_memory.id)
    assert deleted is True
    
    # Verify it's gone - search should not find it
    # Note: ChromaDB may still return results from cached embeddings briefly,
    # so we check by directly querying with get
    results = temp_store.get_by_project(sample_memory.project_id)
    memory_ids = [m.id for m in results]
    assert sample_memory.id not in memory_ids


def test_delete_nonexistent_memory(temp_store):
    """Test deleting a non-existent memory."""
    # Try to delete a memory that doesn't exist
    deleted = temp_store.delete("non_existent_id_12345")
    # Should return False or not raise an exception
    assert deleted in [True, False]


def test_memory_with_relations(temp_store):
    """Test storing and retrieving memories with relations."""
    # Create memory with relations
    memory = Memory(
        id="mem_with_relations",
        content="Memory with relations test",
        entity_type=EntityType.DECISION,
        relations=[
            Relation(target_memory_id="mem_001", relation_type="depends_on", confidence=0.9),
            Relation(target_memory_id="mem_002", relation_type="related_to", confidence=0.7)
        ],
        project_id="test_project"
    )
    
    # Add to store
    temp_store.add(memory)
    
    # Retrieve via search
    results = temp_store.search("Memory with relations", limit=1)
    assert len(results) == 1
    
    retrieved = results[0]
    assert retrieved.id == memory.id
    assert len(retrieved.relations) == 2
    
    # Check relation details
    relation_ids = {r.target_memory_id for r in retrieved.relations}
    assert "mem_001" in relation_ids
    assert "mem_002" in relation_ids


def test_memory_persistence():
    """Test that memories persist across store instances."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create first store and add memory
        store1 = MemoryStore(persist_dir=temp_dir)
        memory = Memory(
            id="persistent_mem",
            content="This memory should persist",
            entity_type=EntityType.FACT,
            project_id="persistence_test"
        )
        store1.add(memory)
        
        # Create new store instance pointing to same directory
        store2 = MemoryStore(persist_dir=temp_dir)
        
        # Should be able to find the memory
        results = store2.get_by_project("persistence_test")
        assert len(results) == 1
        assert results[0].id == "persistent_mem"
        assert results[0].content == "This memory should persist"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
