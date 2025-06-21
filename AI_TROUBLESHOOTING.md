# AI Troubleshooting History

This document tracks our investigation into AI generation issues in spec-cli, documenting problems discovered, solutions attempted, and lessons learned.

## Previous Session Summary (Pre-Context)

### Initial Problem
- `spec gen` command was not creating documentation files in `.specs/` directory
- Command showed "Successfully processed 1 of 1 files" but no files were created
- This was a regression after AI integration - previously generated placeholder content

### Root Cause Investigation Phase 1
**Problem**: Files not being created
- Traced command flow: `gen.py` → `gen_command.py` → `ai_generator.py`
- Found `_execute_single_file()` was calling `generate_with_ai()` which returned content in memory but never wrote files
- `_traditional_template_generation()` was just a stub returning `[target_path]`
- Working `SpecContentGenerator` that actually writes files was never called

**Solution**:
- Updated `_finalize_ai_results()` to extract AI content and write to disk
- Fixed `_traditional_template_generation()` to use `SpecContentGenerator`
- Files now being created successfully

### Template Integration Investigation Phase 2
**User Question**: Are templates being leveraged as AI prompts?
- Templates should be usable as prompt templates
- User concerned AI wasn't using template structure

**Discovery**: AI generation was using hardcoded prompts instead of templates
- Found `AIEnhancedTemplate` class designed for template-to-prompt conversion
- Created `_generate_with_ai_templates()` method for proper template integration
- Added `generate_with_ai_request()` function for template-based requests
- Updated `_create_documentation_prompt()` to use template content
- Created missing `prompt_generator.py` file (though it already existed)

### Final Investigation Results
**Outcome**: Templates ARE being loaded and sent to AI
- Template loading: 695 bytes successfully loaded
- Template-to-prompt conversion: 1960 bytes with AI instructions
- Templates sent to AI provider with source code
- **Root Issue**: AI model (Qwen/Qwen2.5-Coder-0.5B) too small to follow complex template instructions
- Model produces generic content instead of structured template output

**Architecture Status**: ✅ Correct - Templates properly integrated as AI prompts
**Model Limitation**: 0.5B parameters insufficient for reliable template structure following

---

## Current Session Investigation (2025-06-21)

### Session Goal
Test the updated template integration and investigate why AI is generating empty content.

### Phase 1: AI Dependencies Investigation (09:00)

**Problem**: "Local AI provider not available" error when testing

**Investigation**:
```bash
python -c "from spec_cli.ai.providers.local import LocalAIProvider; p = LocalAIProvider(); print(f'Available: {p.is_available()}')"
# Result: Available: False
```

**Root Cause**: Missing AI dependencies
- PyTorch and transformers not installed
- AI dependencies are optional extras in `pyproject.toml`:
  ```toml
  [tool.poetry.extras]
  ai = ["torch", "transformers", "accelerate"]
  ai-full = ["torch", "transformers", "bitsandbytes", "accelerate"]
  ```

**Installation Attempt**:
```bash
poetry install -E ai-full
# Failed: bitsandbytes (0.43.3) not available for macOS ARM64
```

**Solution**: Install basic AI dependencies
```bash
poetry install -E ai  # Success
poetry show | grep -E "torch|transformers"
# torch 2.7.1
# transformers 4.52.4
```

### Phase 2: Provider Availability Bug (09:01)

**Problem**: Even with dependencies installed, provider shows unavailable

**Investigation**: Bug in `get_provider_info()` method
```python
def get_provider_info(self) -> dict[str, object]:
    # Bug: _get_device() called before checking if torch is available
    "device": self._get_device(),  # AssertionError if torch is None
```

**Fix**: Added safety check
```python
"device": self._get_device() if torch is not None else "unavailable",
```

**Verification**: Must use poetry virtual environment
```bash
poetry run python -c "from spec_cli.ai.providers.local import LocalAIProvider; p = LocalAIProvider(); print(f'Available: {p.is_available()}')"
# Result: Available: True
```

### Phase 3: Template Content Analysis (09:02)

**Investigation**: What exactly is being sent to AI?

Created test script to analyze template flow:
```python
# Static Variables (should be pre-filled):
- filename → "calculator.py"
- filepath → "/path/to/file"
- file_extension → "py"
- date → "2025-06-21"
- file_type → "Python module"

# AI Analysis Variables (14 variables):
- purpose, overview, responsibilities
- dependencies, api_interface, example_usage
- configuration, error_handling, testing_notes
- performance_notes, security_notes, etc.
```

**Key Discovery**: AI receives template with placeholders intact
- Before fix: Template with variables already substituted (wrong)
- After fix: Original template with `{{placeholders}}` (correct)
- Template size: 695 bytes sent to AI

### Phase 4: AI Generation Execution Bug (09:02)

**Problem**: AI generation failing with cryptic error

**Debug Logs**:
```
[SPEC DEBUG] AI generation result (success=False, error=Generation failed: cannot access local variable 'normalized_path' where it is not associated with a value)
[SPEC DEBUG] AI generation failed, falling back to enhanced templates
```

**Root Cause**: Variable reference before definition
```python
# Bug in generation.py:131
logger.info(f"Starting AI generation for {normalized_path}")  # normalized_path not defined yet
prompt = self._create_documentation_prompt(request)
# normalized_path defined later in _create_documentation_prompt
```

**Fix**: Define variable before use
```python
normalized_path = normalize_path_separators(str(request.source_file))
logger.info(f"Starting AI generation for {normalized_path}")
```

### Phase 5: Empty Content Investigation (09:03)

**Problem**: AI generation succeeds but produces empty content

**Debug Results**:
```
[SPEC DEBUG] AI generation result (success=True, error=None)
[SPEC DEBUG] AI generation successful, finalizing results
[SPEC DEBUG] AI result data inspection (generated_docs_count=1, generated_docs_keys=['/path/to/calculator.py'])
[SPEC DEBUG] Main content inspection (content_length=0, content_preview=EMPTY, has_content=False)
```

**Analysis**:
- ✅ AI provider loads successfully
- ✅ Template processing works (695 bytes)
- ✅ AI generation completes without error
- ❌ AI output is empty (0 bytes)

### Current Status Summary

**What's Working**:
1. AI dependencies installed correctly
2. AI provider loads and runs
3. Template system processes correctly
4. Templates sent to AI with placeholders intact
5. AI generation pipeline executes without errors

**What's Not Working**:
1. AI model produces empty/minimal content
2. 19 template variables may be too complex for 0.5B model

**Possible Causes**:
1. Model too small for complex template instructions
2. Prompt engineering needs improvement
3. Model parameters (temperature, max_tokens) need tuning
4. Need hybrid approach with pre-filled static variables

### Phase 6: **CRITICAL DISCOVERY** - Dual AI Systems (09:04)

**Root Cause Found**: The system has **TWO DIFFERENT AI SYSTEMS** running simultaneously!

**Debug Logs Revealed**:
```
[SPEC DEBUG] PlaceholderAIProvider initialized
[SPEC DEBUG] AIContentManager initialized (enabled=False)
```

**The Two Systems**:
1. **NEW AI System**: `spec_cli/ai/` - Real LocalAIProvider with PyTorch models
2. **OLD Template AI System**: `spec_cli/templates/ai_integration.py` - PlaceholderAIProvider with fake content

**PlaceholderAIProvider Behavior**:
- Generates fake content like: `"This Python module file 'calculator.py' serves a specific purpose... [AI-generated content would analyze the file]"`
- But `AIContentManager` is initialized with `enabled=False`
- When disabled, returns empty content instead of placeholder text

**Why AI Model Never Loads**:
- The system chooses PlaceholderAIProvider instead of LocalAIProvider
- No actual model loading occurs
- No PyTorch inference happens
- "Success" messages are fake - just placeholder system completing

**Validation Commands**:
```bash
# No model loading logs appear:
SPEC_DEBUG=1 poetry run python -m spec_cli.cli.app gen calculator.py 2>&1 | grep -E "(Loading model|ATTEMPTING TO LOAD)"
# Result: Nothing - proves model never loads

# PlaceholderAIProvider logs do appear:
SPEC_DEBUG=1 poetry run python -m spec_cli.cli.app gen calculator.py 2>&1 | grep "PlaceholderAIProvider"
# Result: [SPEC DEBUG] PlaceholderAIProvider initialized
```

---

## Architecture Issues Identified

### AI Dependencies Structure Problems

**Current Issues**:
1. **Two-stage system confusion**: `ai` vs `ai-full` extras
2. **Optional AI**: AI is central to the tool but treated as optional
3. **Platform-specific failures**: `bitsandbytes` not available on macOS ARM64
4. **Manual environment activation**: Requires `poetry run` to access dependencies

**Proposed Solution**:
- ✅ **IMPLEMENTED**: Make AI dependencies core, not optional
- Remove dual AI system architecture
- Eliminate PlaceholderAIProvider and old template AI system
- Single installation command that "just works"
- Cross-platform compatibility built-in

**New pyproject.toml Structure**:
```toml
[tool.poetry.dependencies]
# Core AI dependencies - no more optional/extras
torch = "^2.0.0"
transformers = "^4.40.0"
accelerate = "^0.30.0"
# bitsandbytes excluded - not available on macOS ARM64
```

### Template System Complexity

**Current State**:
- AI receives 19 template variables to fill
- Small model (0.5B) struggles with complex instructions
- Template structure: Static info + Content analysis mixed together

**Proposed Hybrid Approach**:
- Pre-fill static variables (filename, date, file_type, etc.)
- AI only analyzes code for content variables (purpose, overview, dependencies)
- Reduce AI task from 19 variables to ~14 variables
- Clearer, more focused AI instructions

---

## Next Steps

### **IMMEDIATE (Critical Fix)**
1. ✅ **Make AI Dependencies Core**: Updated pyproject.toml to include torch/transformers as required
2. ✅ **Eliminate Dual AI Systems**: Disabled PlaceholderAIProvider, forced new AI system
3. ✅ **Force Real AI Provider**: LocalAIProvider is now selected (not placeholder!)
4. 🔄 **Test Actual Model Loading**: AI provider selected but model not loading

### **BREAKTHROUGH: Real AI System Now Working** (09:50)
```
DEBUG: AI config loaded: enabled=True, provider=local
DEBUG: Selected AI provider: LocalAIProvider
DEBUG: Provider result: success=True, error=None
```

**What's Fixed**:
- ✅ Dual AI systems eliminated
- ✅ LocalAIProvider correctly selected
- ✅ New AI flow: gen_command → ai_generator → LocalAIProvider
- ✅ Core AI dependencies working

**Remaining Issue**:
- ❌ AI model not loading ("ATTEMPTING TO LOAD" never appears)
- ❌ Provider returns success=True but empty content
- ❌ No index.md files created (content_length=0)

### **CURRENT SESSION: Model Loading Root Cause Investigation (2025-06-21 10:00)**

**MAJOR BREAKTHROUGH: AI Model Loading Issue RESOLVED**

After systematic debugging with print trace statements, discovered the complete flow is working but AI model is generating immediate EOS token.

**What's Now Working (Confirmed with Debug Traces)**:
1. ✅ **LocalAIProvider.generate_documentation()** correctly called
2. ✅ **DocumentationGenerator.load_model()** successfully loads Qwen2.5-Coder-0.5B model in 1.1s on MPS
3. ✅ **PyTorch model inference** executes successfully with proper tokenization
4. ✅ **Template processing** creates 3993-character prompt correctly
5. ✅ **Model generation** completes with proper device (mps) and configuration

**Root Cause Found - AI Model Output Issue**:
- **Input**: 936 tokens (3993 characters prompt)
- **Generation**: Model generates exactly **1 token** (ID: 151645)
- **Token Type**: This is the **EOS (end-of-sequence) token** `<|im_end|>`
- **Result**: After removing special tokens, content is empty

**Debug Evidence**:
```
PRINT TRACE: Tokenized input shape: torch.Size([1, 936])
PRINT TRACE: Model generation completed, output shape: torch.Size([1, 937])
PRINT TRACE: Generated token IDs: [151645]
PRINT TRACE: EOS token ID: 151645
PRINT TRACE: Generated text with special tokens: '<|im_end|>'
PRINT TRACE: Generated text without special tokens: ''
```

**Analysis**: The Qwen2.5-Coder model is **immediately ending generation** without producing content. This suggests:
1. **Prompt format incompatibility** with the model's expected format
2. **Model thinks the prompt is already complete** and doesn't need to generate
3. **0.5B model may be too small** for complex template-driven prompts (3993 chars)

**Next Investigation Steps**:
1. **Examine the actual prompt** being sent to see if format is correct for Qwen2.5-Coder
2. **Test with simpler, shorter prompts** to verify model can generate content
3. **Check Qwen2.5-Coder documentation** for proper prompt format
4. **Consider model size upgrade** from 0.5B to 1B+ if prompt format is correct

### **SHORT TERM**
5. **Fix Model Loading**: Ensure PyTorch model actually loads and runs inference
6. **Implement Hybrid Templates**: Pre-fill static variables to reduce AI complexity
7. **Cross-platform Testing**: Ensure works on Windows, macOS, Linux

### **MEDIUM TERM**
8. **Test Model Performance**: Verify if real AI model produces meaningful output
9. **Consider Model Size**: If 0.5B insufficient, evaluate 1B+ models
10. **Optimize Prompting**: Improve prompt engineering for small models

---

## Key Files and Functions

### AI Generation Flow
- `spec_cli/cli/commands/gen_command.py:_execute_single_file()` - Main execution logic
- `spec_cli/cli/commands/gen_command.py:_generate_with_ai_templates()` - AI template integration
- `spec_cli/ai/generation/ai_generator.py:generate_with_ai_request()` - AI request handling
- `spec_cli/ai/providers/generation.py:generate_documentation()` - AI model execution
- `spec_cli/ai/providers/generation.py:_create_documentation_prompt()` - Prompt creation

### Template System
- `spec_cli/templates/ai_enhanced.py:AIEnhancedTemplate` - Template-to-prompt conversion
- `spec_cli/templates/prompt_generator.py:PromptGenerator` - Template analysis
- `spec_cli/templates/defaults.py` - Default template definitions

### Provider Management
- `spec_cli/ai/providers/local.py:LocalAIProvider` - Local AI model handling
- `spec_cli/ai/providers/manager.py:ProviderManager` - Provider selection logic

---

## Testing Commands

### Verify AI Dependencies are Core (Not Optional)
```bash
# Check dependencies are installed as core
poetry show | grep -E "torch|transformers|accelerate"
# Should show: torch 2.7.1, transformers 4.52.4, accelerate 0.X.X

# Verify no optional extras needed
poetry install  # Should install everything including AI
```

### Test Real AI Model Loading
```bash
# Check if REAL AI model loads (should see "ATTEMPTING TO LOAD AI MODEL")
SPEC_DEBUG=1 poetry run python -m spec_cli.cli.app gen <file.py> 2>&1 | grep -E "(ATTEMPTING TO LOAD|Loading model)"

# Verify PlaceholderAIProvider is NOT used
SPEC_DEBUG=1 poetry run python -m spec_cli.cli.app gen <file.py> 2>&1 | grep "PlaceholderAIProvider"
# Should return nothing if fixed

# Check which provider is selected
SPEC_DEBUG=1 poetry run python -m spec_cli.cli.app gen <file.py> 2>&1 | grep "Selected AI provider"
# Should show "LocalAIProvider", not "None"
```

### Verify Model Performance
```bash
# Test if AI generates actual content (not empty)
SPEC_DEBUG=1 poetry run python -m spec_cli.cli.app gen calculator.py 2>&1 | grep "Main content inspection"
# Should show content_length > 0, not "EMPTY"

# Check generated files
ls -la .specs/calculator/
# Should contain both index.md AND history.md with content
```

---

## **SESSION HANDOFF: Next Steps**

### **Immediate Next Session Focus**

The dual AI system issue has been **RESOLVED**. LocalAIProvider is now correctly selected and the new AI architecture is working. However, the AI model is not actually loading and generating content.

**Status Summary**:
- ✅ **Architecture Fixed**: Real AI system (LocalAIProvider) now used instead of PlaceholderAIProvider
- ✅ **Dependencies Fixed**: Core AI dependencies (torch, transformers) installed successfully
- ✅ **Flow Working**: Complete execution from gen_command → ai_generator → LocalAIProvider
- ❌ **Model Loading Missing**: PyTorch model not loading despite successful provider calls

### **Next Session Starting Point**

**Immediate Task**: Investigate why `DocumentationGenerator.load_model()` is not being called despite LocalAIProvider executing successfully.

**Debug Strategy**:
1. Add debug prints to `spec_cli/ai/providers/local.py:generate_documentation()` method
2. Trace execution path to see if `DocumentationGenerator` is created and used
3. Check if model loading is bypassed due to availability checks or other logic
4. Verify torch/transformers can instantiate the Qwen2.5-Coder model directly

**Test File Ready**: `/Users/spensermcconnell/__Active_Code/spec-cli/test_demo/test_demo/calculator.py`

**Expected Outcome**: See "ATTEMPTING TO LOAD AI MODEL" logs and generate actual content in `.specs/calculator/index.md`
