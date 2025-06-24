"""Template system for spec CLI.

This package provides template configuration, loading, substitution, and content generation
for creating consistent documentation across different contexts, with AI integration support.
"""

from .ai_enhanced import AIEnhancedTemplate, TemplateResult, create_ai_enhanced_template
from .ai_integration import (
    AIContentManager,
    AIContentProvider,
    MockAIProvider,
    ai_content_manager,
    ask_llm,
    retry_with_backoff,
)
from .config import TemplateConfig, TemplateValidator
from .defaults import get_default_template_config, get_template_preset
from .generator import SpecContentGenerator, generate_spec_content
from .loader import TemplateLoader, load_template
from .prompt_generator import (
    PromptGenerator,
    PromptStructure,
    convert_template_to_prompt,
)
from .substitution import TemplateSubstitution

__all__ = [
    "TemplateConfig",
    "TemplateValidator",
    "TemplateLoader",
    "load_template",
    "get_default_template_config",
    "get_template_preset",
    "TemplateSubstitution",
    "SpecContentGenerator",
    "generate_spec_content",
    "AIContentProvider",
    "MockAIProvider",
    "AIContentManager",
    "ai_content_manager",
    "ask_llm",
    "retry_with_backoff",
    "PromptGenerator",
    "PromptStructure",
    "convert_template_to_prompt",
    "AIEnhancedTemplate",
    "TemplateResult",
    "create_ai_enhanced_template",
]
