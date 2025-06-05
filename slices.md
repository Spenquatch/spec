Security Vulnerability Fix - Slice Generation

  Slice 1a: Git Command Whitelist Validator

  Goal: Implement secure git command validation to prevent command
  injection attacks

  Slice Type: Infrastructure

  Helper Dependencies & Search Evidence:
  - Helper search performed: grep -r
  "def.*validat.*input\|def.*sanitiz\|def.*whitelist" spec_cli/utils
  No matches found for input validation/sanitization

  - Helper search performed: grep -r
  "def.*safe_relative_to\|def.*validate_path" spec_cli/
  Found existing: spec_cli/utils/path_utils.py

  - Existing helper: spec_cli/utils/path_utils.py → safe_relative_to()
  for secure path validation
  - Existing helper: spec_cli/utils/error_utils.py →
  handle_subprocess_error() for secure error formatting
  - New helper to create: spec_cli/utils/security_validators.py →
  validate_git_command(cmd: List[str]) -> bool

  Complexity Analysis:
  - Decision points: 4/7 (command whitelist check, argument validation,
  path validation, error handling)
  - Helper calls: 2 (safe_relative_to, handle_subprocess_error)
  - McCabe validation: Pass (4 ≤ 7 with helper abstraction)

  Inputs → Action → Outputs:
  - Inputs: {git_args: List[str], work_tree_path: Path}
  - Action:
    a. Create security_validators.py with whitelist of safe git commands
    b. Validate git command against whitelist (add, commit, status, log,
   diff, show, init)
    c. Sanitize file path arguments using safe_relative_to() with
  strict=True
    d. Return validation result with specific error context
  - Outputs: {is_valid: bool, error_message: Optional[str]}

  Files to Create/Modify:
  - Create: spec_cli/utils/security_validators.py (git command
  validation)
  - Test: test_slice_1a.py

  Test Requirements:
  - Unit Tests: Test whitelist validation with valid/invalid commands,
  path injection attempts (100% coverage)
  - Integration Test: Validate against actual git commands used in
  GitOperations
  - Idempotent Tests: Security validation results consistent across runs
  - Mocks/Fixtures: Mock Path objects for controlled path validation
  scenarios

  Quality Gate Validation:
  - poetry run mypy --strict (zero suppressions for security code)
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pydocstyle (Google-style docstrings)
  - poetry run bandit -r spec_cli/utils/security_validators.py (zero
  high-severity findings)
  - poetry run pytest -v --cov=spec_cli --cov-fail-under=90

  Integration Validation:
  End-to-end test: validate_git_command() rejects malicious commands and
   accepts only whitelisted operations

  AI Agent Execution Notes:
  - Focus on comprehensive command whitelist covering all legitimate
  spec operations
  - Ensure path validation prevents directory traversal attacks
  - Use secure error messages that don't leak sensitive information

  ---
  Slice 1b: Secure Git Operations Integration

  Goal: Integrate command validation into GitOperations to eliminate
  injection vulnerability

  Slice Type: Integration

  Helper Dependencies & Search Evidence:
  - Helper search performed: grep -r "validate_git_command"
  spec_cli/utils/
  Will be available from Slice 1a

  - Existing helper: spec_cli/utils/security_validators.py →
  validate_git_command() (from Slice 1a)
  - Existing helper: spec_cli/utils/error_utils.py →
  handle_subprocess_error() for safe error reporting
  - Existing helper: spec_cli/utils/path_utils.py → safe_relative_to()
  for path validation

  Complexity Analysis:
  - Decision points: 3/7 (validation check, error handling, command
  execution)
  - Helper calls: 3 (validate_git_command, safe_relative_to,
  handle_subprocess_error)
  - McCabe validation: Pass (3 ≤ 7 with extensive helper usage)

  Inputs → Action → Outputs:
  - Inputs: {git_args: List[str], capture_output: bool}
  - Action:
    a. Validate git command using
  security_validators.validate_git_command()
    b. Apply path validation to any file arguments
    c. Execute command only if validation passes
    d. Use secure error handling that doesn't expose sensitive
  information
  - Outputs: {CompletedProcess[str]} or {SpecGitError with sanitized
  message}

  Files to Create/Modify:
  - Modify: spec_cli/git/operations.py (integrate validation into
  run_git_command)
  - Test: test_slice_1b.py

  Test Requirements:
  - Unit Tests: Test command validation integration, error handling
  paths (100% coverage)
  - Integration Test: Execute safe git commands, verify malicious
  commands are blocked
  - Idempotent Tests: Git operations remain secure across multiple calls
  - Mocks/Fixtures: Mock subprocess for testing command rejection
  scenarios

  Quality Gate Validation:
  - poetry run mypy --strict (clean integration with existing types)
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run bandit -r spec_cli/git/operations.py (zero high-severity
  findings)
  - poetry run pytest tests/unit/git/test_slice_1b.py -v

  Integration Validation:
  End-to-end test: GitOperations.run_git_command() successfully blocks
  injection attempts while allowing legitimate operations

  AI Agent Execution Notes:
  - Preserve existing functionality while adding security layer
  - Ensure error messages are informative but don't leak system
  information
  - Maintain backward compatibility with existing GitOperations callers

  ---
  Slice 1c: Error Message Sanitization

  Goal: Sanitize error messages to prevent information disclosure
  through git command failures

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: grep -r
  "def.*sanitize.*error\|def.*safe.*message" spec_cli/utils/
  No matches found for error sanitization

  - Existing helper: spec_cli/utils/error_utils.py →
  handle_subprocess_error() for error formatting
  - New helper to create: spec_cli/utils/security_validators.py →
  sanitize_error_message(msg: str) -> str

  Complexity Analysis:
  - Decision points: 5/7 (sensitive pattern detection, path
  sanitization, command sanitization, context filtering)
  - Helper calls: 1 (handle_subprocess_error)
  - McCabe validation: Pass (5 ≤ 7 with helper usage)

  Inputs → Action → Outputs:
  - Inputs: {error_message: str, command_context: Optional[str]}
  - Action:
    a. Extend security_validators.py with error message sanitization
    b. Remove absolute paths from error messages
    c. Filter out potentially sensitive command arguments
    d. Preserve actionable error information for debugging
  - Outputs: {sanitized_message: str}

  Files to Create/Modify:
  - Modify: spec_cli/utils/security_validators.py (add
  sanitize_error_message function)
  - Modify: spec_cli/utils/error_handler.py (integrate sanitization)
  - Test: test_slice_1c.py

  Test Requirements:
  - Unit Tests: Test sanitization with various error message patterns
  (100% coverage)
  - Integration Test: Verify sanitization works with actual git error
  scenarios
  - Idempotent Tests: Sanitization produces consistent results
  - Mocks/Fixtures: Mock error scenarios with sensitive information

  Quality Gate Validation:
  - poetry run mypy --strict (complete type coverage for security
  functions)
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run bandit -r spec_cli/utils/ (zero high-severity findings)
  - poetry run pytest tests/unit/utils/test_slice_1c.py -v

  Integration Validation:
  End-to-end test: Error messages from git operations contain no
  absolute paths or sensitive command details

  AI Agent Execution Notes:
  - Balance between security and debuggability in error messages
  - Focus on patterns that commonly appear in git error output
  - Ensure sanitization doesn't break existing error handling workflows
