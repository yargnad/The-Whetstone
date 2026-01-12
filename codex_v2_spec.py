"""
CODEX v2.0 Specification Module

Defines the structure and utilities for CODEX persona files with embedded
source texts and AI filtering recipes.

Version History:
- v1.0: Metadata-only (name, description, prompt, library_filter)
- v2.0: Full-fidelity with source_texts and recipes layers
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import json


class TextBoundary(BaseModel):
    """Marks the start/end of author content within a source text."""
    start_marker: Optional[str] = Field(None, description="First phrase of author content")
    end_marker: Optional[str] = Field(None, description="Last phrase or 'THE END'")
    start_offset: Optional[int] = Field(None, description="Character offset where content starts")
    end_offset: Optional[int] = Field(None, description="Character offset where content ends")


class SourceText(BaseModel):
    """A complete source text embedded in the CODEX."""
    title: str = Field(..., description="Work title")
    author: str = Field(..., description="Author name")
    content: str = Field(..., description="Full text content")
    boundaries: Optional[TextBoundary] = Field(None, description="Curated content boundaries")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class Recipe(BaseModel):
    """Instructions for filtering non-author content from source texts."""
    pattern_type: str = Field(..., description="Type: 'structural', 'ai_filter', 'regex'")
    action: str = Field(..., description="Action: 'remove', 'replace', 'extract'")
    markers: Optional[List[str]] = Field(None, description="Structural markers to detect")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern for matching")
    model_used: Optional[str] = Field(None, description="AI model for filtering")
    prompt_hash: Optional[str] = Field(None, description="Hash of AI prompt used")
    confidence: Optional[float] = Field(None, description="Confidence score 0-1")
    reason: Optional[str] = Field(None, description="Human-readable explanation")
    recipe_version: str = Field("2.0", description="Recipe format version")


class CoreLayer(BaseModel):
    """Core persona configuration."""
    system_prompt: str = Field(..., description="Generated persona prompt")
    custom_preamble: Optional[str] = Field("", description="User-added custom instructions")


class CodexMetadata(BaseModel):
    """CODEX file metadata."""
    name: str = Field(..., description="Persona name")
    description: Optional[str] = Field("", description="Brief description")
    author: Optional[str] = Field(None, description="Original author")
    creator: Optional[str] = Field(None, description="CODEX creator/curator")
    created: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    version: str = Field("2.0", description="CODEX format version")


class CodexLayers(BaseModel):
    """All layers in the CODEX file."""
    core: CoreLayer = Field(..., description="Core persona configuration")
    source_texts: Optional[List[SourceText]] = Field(default_factory=list, description="Embedded source texts")
    recipes: Optional[List[Recipe]] = Field(default_factory=list, description="Curation recipes")


class CodexV2(BaseModel):
    """Complete CODEX v2.0 persona file structure."""
    format: str = Field("codex/persona", description="Format identifier")
    version: str = Field("2.0", description="CODEX spec version")
    metadata: CodexMetadata = Field(..., description="Persona metadata")
    layers: CodexLayers = Field(..., description="All persona layers")

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent, exclude_none=True)

    @classmethod
    def from_json(cls, json_str: str) -> "CodexV2":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)

    @classmethod
    def from_file(cls, filepath: str) -> "CodexV2":
        """Load from .codex file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

    def to_file(self, filepath: str) -> None:
        """Save to .codex file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    def is_v1_compatible(self) -> bool:
        """Check if can be downgraded to v1.0 (metadata-only)."""
        return (
            len(self.layers.source_texts or []) == 0 and
            len(self.layers.recipes or []) == 0
        )

    def to_v1(self) -> Dict[str, Any]:
        """Convert to v1.0 format (metadata only, for backward compatibility)."""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "prompt": self.layers.core.system_prompt,
            "library_filter": [self.metadata.author] if self.metadata.author else []
        }


# Utility functions

def create_minimal_codex(name: str, prompt: str, author: Optional[str] = None) -> CodexV2:
    """Create a minimal v2.0 CODEX (no texts or recipes)."""
    return CodexV2(
        metadata=CodexMetadata(
            name=name,
            author=author or name,
            description=f"Persona based on {author or name}"
        ),
        layers=CodexLayers(
            core=CoreLayer(system_prompt=prompt)
        )
    )


def validate_codex(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate CODEX data structure.
    Returns: (is_valid, error_message)
    """
    try:
        CodexV2.model_validate(data)
        return (True, "")
    except Exception as e:
        return (False, str(e))


def detect_version(data: Dict[str, Any]) -> str:
    """
    Detect CODEX version from data structure.
    Returns: "1.0", "2.0", or "unknown"
    """
    # v2.0 has explicit version field
    if data.get("version") == "2.0" and data.get("format") == "codex/persona":
        return "2.0"
    
    # v1.0 has simple structure: name, prompt, library_filter
    if "name" in data and "prompt" in data and "layers" not in data:
        return "1.0"
    
    return "unknown"


def upgrade_v1_to_v2(v1_data: Dict[str, Any]) -> CodexV2:
    """Convert v1.0 CODEX to v2.0 format."""
    return CodexV2(
        metadata=CodexMetadata(
            name=v1_data.get("name", "Unknown"),
            description=v1_data.get("description", ""),
            author=v1_data.get("library_filter", [None])[0]
        ),
        layers=CodexLayers(
            core=CoreLayer(
                system_prompt=v1_data.get("prompt", ""),
                custom_preamble=v1_data.get("custom_preamble", "")
            ),
            source_texts=[],
            recipes=[]
        )
    )
