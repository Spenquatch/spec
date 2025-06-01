"""Generation command utilities and workflows.

This package provides shared utilities for generation commands including
workflow coordination, user prompts, and validation.
"""

from .workflows import (
    GenerationWorkflow,
    RegenerationWorkflow,
    AddWorkflow,
    create_generation_workflow,
    create_regeneration_workflow,
    create_add_workflow,
)
from .prompts import (
    TemplateSelector,
    ConflictResolver,
    GenerationPrompts,
    select_template,
    resolve_conflicts,
    confirm_generation,
)
from .validation import (
    GenerationValidator,
    validate_generation_input,
    validate_template_selection,
    validate_file_paths,
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
