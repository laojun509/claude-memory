from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    PROJECT = "project"
    CODE_STYLE = "code_style"
    DECISION = "decision"
    TASK = "task"


class Relation(BaseModel):
    target_memory_id: str
    relation_type: str
    confidence: float = Field(ge=0.0, le=1.0)


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: f"mem_{datetime.now().timestamp()}")
    content: str
    embedding: Optional[List[float]] = None
    entity_type: EntityType
    relations: List[Relation] = Field(default_factory=list)
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    project_id: str = "default"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
