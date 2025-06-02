"""Generation command utilities and workflows.

This package provides shared utilities for generation commands including
workflow coordination, user prompts, and validation.
"""

from .prompts import (
    ConflictResolver,
    GenerationPrompts,
    TemplateSelector,
    confirm_generation,
    resolve_conflicts,
    select_template,
)
from .validation import (
    GenerationValidator,
    validate_file_paths,
    validate_generation_input,
    validate_template_selection,
)
from .workflows import (
    AddWorkflow,
    GenerationWorkflow,
    RegenerationWorkflow,
    create_add_workflow,
    create_generation_workflow,
    create_regeneration_workflow,
)

__all__ = [
    "GenerationWorkflow",
    "RegenerationWorkflow",
    "AddWorkflow",
    "create_generation_workflow",
    "create_regeneration_workflow",
    "create_add_workflow",
    "TemplateSelector",
    "ConflictResolver",
    "GenerationPrompts",
    "select_template",
    "resolve_conflicts",
    "confirm_generation",
    "GenerationValidator",
    "validate_generation_input",
    "validate_template_selection",
    "validate_file_paths",
]
