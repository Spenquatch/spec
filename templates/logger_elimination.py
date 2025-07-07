"""Template for Logger Singleton Elimination

This template shows the before/after patterns for eliminating logger singletons.
"""

# ===== BEFORE: Singleton Pattern =====

from spec_cli.logging.debug import debug_logger

def old_analyze_pattern(file_path):
    """OLD: Function using singleton logger access."""
    # Anti-pattern: Global singleton logger
    debug_logger.log("INFO", "Starting pattern analysis", file_path=str(file_path))
    
    try:
        patterns = []
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Analysis logic
        if 'class' in content and '__new__' in content:
            debug_logger.log("DEBUG", "Found potential singleton pattern", 
                           pattern_type="metaclass", line_count=len(content.split('\n')))
            patterns.append("singleton")
        
        debug_logger.log("INFO", "Pattern analysis completed", 
                        patterns_found=len(patterns))
        return patterns
        
    except Exception as e:
        debug_logger.log("ERROR", "Pattern analysis failed", 
                        error=str(e), file_path=str(file_path))
        raise

def old_helper_function(data):
    """Helper function also using singleton logger."""
    # Anti-pattern: Nested singleton access
    debug_logger.log("DEBUG", "Processing data", data_type=type(data).__name__)
    
    # Processing logic here
    result = len(data) if hasattr(data, '__len__') else 1
    
    debug_logger.log("DEBUG", "Data processed", result_size=result)
    return result

# ===== AFTER: Injected Logger Pattern =====

from spec_cli.core.context import SpecContext

def new_analyze_pattern(file_path, context: SpecContext):
    """NEW: Function using injected logger."""
    # Target pattern: Logger through context
    logger = context.logger
    
    logger.log("INFO", "Starting pattern analysis", file_path=str(file_path))
    
    try:
        patterns = []
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Analysis logic
        if 'class' in content and '__new__' in content:
            logger.log("DEBUG", "Found potential singleton pattern", 
                      pattern_type="metaclass", line_count=len(content.split('\n')))
            patterns.append("singleton")
        
        logger.log("INFO", "Pattern analysis completed", 
                  patterns_found=len(patterns))
        return patterns
        
    except Exception as e:
        logger.log("ERROR", "Pattern analysis failed", 
                  error=str(e), file_path=str(file_path))
        raise

def new_helper_function(data, logger):
    """Helper function with injected logger."""
    # Target pattern: Logger passed as parameter
    logger.log("DEBUG", "Processing data", data_type=type(data).__name__)
    
    # Processing logic here
    result = len(data) if hasattr(data, '__len__') else 1
    
    logger.log("DEBUG", "Data processed", result_size=result)
    return result

# Alternative: Helper with context
def new_helper_with_context(data, context: SpecContext):
    """Helper function with full context."""
    # Target pattern: Logger through context
    logger = context.logger
    return new_helper_function(data, logger)

# ===== CONTEXT LOGGER SETUP =====

import logging
from spec_cli.logging.formatter import SpecFormatter

class SpecContext:
    """Context with logger management."""
    
    def __init__(self, debug_mode=False):
        self._debug_mode = debug_mode
        self._logger = None
    
    @property
    def logger(self):
        """Lazy-loaded logger with proper configuration."""
        if self._logger is None:
            self._logger = self._create_logger()
        return self._logger
    
    def _create_logger(self):
        """Create configured logger instance."""
        logger = logging.getLogger(f"spec_cli.{id(self)}")
        
        # Configure logger based on context settings
        level = logging.DEBUG if self._debug_mode else logging.INFO
        logger.setLevel(level)
        
        # Add context-specific handler
        handler = logging.StreamHandler()
        handler.setFormatter(SpecFormatter())
        logger.addHandler(handler)
        
        return logger

# ===== MIGRATION STEPS =====

"""
Step 1: Update Context
- Add logger property to context
- Configure logger based on context settings (debug mode, etc.)
- Support logger hierarchy and formatting

Step 2: Update Function Signatures
- Add context parameter to functions needing logging
- For utility functions, choose between:
  a) Accept logger parameter directly
  b) Accept full context and extract logger

Step 3: Replace Logger Access
- Remove all debug_logger imports
- Replace debug_logger.log() with context.logger.log()
- Maintain same logging calls and structured data

Step 4: Update Utility Functions
- Pass logger or context to utility functions
- Avoid global logger access in utilities
- Consider logger parameter vs full context based on function needs

Step 5: Update Tests
- Use mock logger in test context
- Validate logging calls and structured data
- Test logger configuration and hierarchy
"""

# ===== TEST MIGRATION EXAMPLE =====

# OLD TEST:
def test_old_analyze_pattern():
    """OLD: Test with global logger mocking."""
    from unittest.mock import patch
    
    # Anti-pattern: Mock global logger
    with patch('spec_cli.logging.debug.debug_logger') as mock_logger:
        result = old_analyze_pattern(Path('test.py'))
        
        mock_logger.log.assert_called_with("INFO", "Starting pattern analysis", 
                                         file_path="test.py")
        assert len(result) >= 0

# NEW TEST:
def test_new_analyze_pattern():
    """NEW: Test with injected mock logger."""
    from unittest.mock import Mock
    
    # Target pattern: Mock logger through context
    mock_logger = Mock()
    context = Mock()
    context.logger = mock_logger
    
    result = new_analyze_pattern(Path('test.py'), context)
    
    mock_logger.log.assert_called_with("INFO", "Starting pattern analysis", 
                                     file_path="test.py")
    assert len(result) >= 0

# FIXTURE EXAMPLE:
@pytest.fixture
def context_with_logger():
    """Test fixture providing context with configured logger."""
    context = SpecContext(debug_mode=True)
    
    # Override logger for testing
    mock_logger = Mock()
    context._logger = mock_logger
    
    return context, mock_logger

def test_with_fixture(context_with_logger):
    """Test using logger fixture."""
    context, mock_logger = context_with_logger
    
    new_analyze_pattern(Path('test.py'), context)
    
    # Validate logging calls
    assert mock_logger.log.call_count > 0