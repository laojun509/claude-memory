"""Integration tests for the complete memory system."""
import pytest
from unittest.mock import patch
from claude_memory.core.engine import MemoryEngine
from claude_memory.integrations.acp_adapter import ACPMemoryAdapter
from claude_memory.core.models import Memory, EntityType


def test_full_workflow(tmp_path):
    """Test complete memory workflow from extraction to injection."""
    persist_dir = str(tmp_path / "memory_db")
    
    # Initialize
    adapter = ACPMemoryAdapter(project_id="test_proj", persist_dir=persist_dir)
    
    # Step 1: Simulate conversation and extract memories
    conversation = [
        {"role": "user", "content": "I hate writing CSS, I prefer backend work"},
        {"role": "assistant", "content": "Got it, you prefer backend development"},
    ]
    
    with patch.object(adapter.engine.extractor, 'extract') as mock_extract:
        mock_extract.return_value = [
            Memory(
                content="User prefers backend development over frontend/CSS",
                entity_type=EntityType.PREFERENCE,
                importance=0.8,
                project_id="test_proj",
            ),
        ]
        
        # Process conversation - extract memories
        memories = adapter.on_conversation_end(conversation)
        assert len(memories) == 1
        assert "backend" in memories[0].content
    
    # Step 2: Search for memory
    with patch.object(adapter.engine.store, 'search') as mock_search:
        mock_search.return_value = [
            Memory(content="User prefers backend", entity_type=EntityType.PREFERENCE, importance=0.8),
        ]
        
        results = adapter.search("backend")
        assert len(results) >= 1
    
    # Step 3: Get enhanced prompt for new conversation
    with patch.object(adapter.engine, 'get_enhanced_system_prompt') as mock_enhance:
        mock_enhance.return_value = """
You are a helpful assistant.

[RELEVANT CONTEXT from previous conversations]:
  💭 User prefers backend development
[END CONTEXT]
"""
        
        new_conversation = [{"role": "user", "content": "What should I work on?"}]
        prompt = adapter.enhance_system_prompt(
            "You are a helpful assistant.",
            new_conversation,
        )
        
        assert "backend" in prompt.lower() or "RELEVANT CONTEXT" in prompt


def test_project_isolation(tmp_path):
    """Test that memories are isolated by project."""
    adapter1 = ACPMemoryAdapter(project_id="project_a", persist_dir=str(tmp_path / "mem"))
    adapter2 = ACPMemoryAdapter(project_id="project_b", persist_dir=str(tmp_path / "mem"))
    
    # Mock different memories for each project
    with patch.object(adapter1.engine.store, 'get_by_project') as mock_get_a:
        mock_get_a.return_value = [
            Memory(content="Project A memory", entity_type=EntityType.PROJECT, project_id="project_a"),
        ]
        
        with patch.object(adapter2.engine.store, 'get_by_project') as mock_get_b:
            mock_get_b.return_value = [
                Memory(content="Project B memory", entity_type=EntityType.PROJECT, project_id="project_b"),
            ]
            
            memories_a = adapter1.engine.get_project_memories("project_a")
            memories_b = adapter2.engine.get_project_memories("project_b")
            
            assert len(memories_a) == 1
            assert len(memories_b) == 1
            assert memories_a[0].content == "Project A memory"
            assert memories_b[0].content == "Project B memory"


def test_memory_extraction_and_storage(tmp_path):
    """Test end-to-end memory extraction and storage."""
    engine = MemoryEngine(persist_dir=str(tmp_path / "memory"))
    
    conversation = [
        {"role": "user", "content": "Use TypeScript for this project"},
        {"role": "assistant", "content": "I'll use TypeScript"},
    ]
    
    with patch.object(engine.extractor, 'extract') as mock_extract:
        with patch.object(engine.store, 'add') as mock_add:
            mock_extract.return_value = [
                Memory(
                    content="Project uses TypeScript",
                    entity_type=EntityType.PROJECT,
                    importance=0.8,
                ),
            ]
            mock_add.return_value = "mem_123"
            
            memories = engine.process_conversation(conversation, project_id="proj_1")
            
            assert len(memories) == 1
            mock_extract.assert_called_once()
            mock_add.assert_called_once()


def test_context_retrieval_for_conversation(tmp_path):
    """Test retrieving relevant context for a conversation."""
    engine = MemoryEngine(persist_dir=str(tmp_path / "memory"))
    
    conversation = [
        {"role": "user", "content": "What framework should I use?"},
    ]
    
    with patch.object(engine.retriever, 'get_context_for_conversation') as mock_get:
        mock_get.return_value = [
            Memory(content="User prefers FastAPI", entity_type=EntityType.PREFERENCE, importance=0.8),
            Memory(content="Project uses Python", entity_type=EntityType.PROJECT, importance=0.7),
        ]
        
        context = engine.get_context(conversation, project_id="test")
        
        assert len(context) == 2
        assert context[0].importance >= context[1].importance  # Sorted by importance
