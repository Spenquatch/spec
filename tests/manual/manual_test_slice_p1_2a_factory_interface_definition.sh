#!/bin/bash
# Manual Test Script: Slice P1.2a - Factory Interface Definition
# Purpose: Manually verify that the factory interface and environment detection work correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P1.2a - Factory Interface Definition ==="
echo "Purpose: Validate factory interface definition and environment detection functionality"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python is not available"
    exit 1
fi

if ! python -c "import sys; sys.path.append('spec_cli')" 2>/dev/null; then
    echo "WARNING: spec_cli module may not be properly accessible"
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
export PYTHONPATH="${PWD}:${PYTHONPATH}"
cd "${PWD}"
echo "Working directory: $(pwd)"
echo "Python path: ${PYTHONPATH}"
echo "Test environment ready"
echo

# Test execution phase
echo "Executing manual tests..."

# Test 1: Environment Detection Functionality
echo ""
echo "Test 1: Environment Detection in Various Contexts"
echo "Expected: Different environment types detected based on context"
echo "Executing:"

echo "  Testing default environment detection:"
ENV_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.utils.factory_utils import detect_environment_type
result = detect_environment_type()
print(f'Environment detected: {result}')
print(f'Result type: {type(result).__name__}')
")
echo "  Result: $ENV_RESULT"

echo "  Testing with SPEC_ENV=testing:"
SPEC_ENV_RESULT=$(SPEC_ENV=testing python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.utils.factory_utils import detect_environment_type
result = detect_environment_type()
print(f'Environment detected: {result}')
")
echo "  Result: $SPEC_ENV_RESULT"

echo "  Testing with TESTING=1:"
TESTING_ENV_RESULT=$(TESTING=1 python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.utils.factory_utils import detect_environment_type
result = detect_environment_type()
print(f'Environment detected: {result}')
")
echo "  Result: $TESTING_ENV_RESULT"

if [[ $SPEC_ENV_RESULT == *"testing"* && $TESTING_ENV_RESULT == *"testing"* ]]; then
    echo "Status: PASS - Environment detection working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Environment detection not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

# Test 2: Factory Input Validation
echo "Test 2: Factory Input Validation"
echo "Expected: Valid inputs processed correctly, invalid inputs raise appropriate errors"
echo "Executing:"

echo "  Testing valid factory inputs:"
VALID_INPUTS_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.utils.factory_utils import validate_factory_inputs
try:
    result = validate_factory_inputs(
        factory_type='context',
        timeout=30,
        debug_mode=True,
        factory_config={'key': 'value'}
    )
    print(f'Validation successful: {len(result)} parameters validated')
    print(f'Factory type: {result.get(\"factory_type\")}')
    print(f'Timeout: {result.get(\"timeout\")}')
    print(f'Debug mode: {result.get(\"debug_mode\")}')
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $VALID_INPUTS_RESULT"

echo "  Testing invalid factory inputs (empty factory_type):"
INVALID_INPUTS_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.utils.factory_utils import validate_factory_inputs
try:
    result = validate_factory_inputs(factory_type='')
    print(f'UNEXPECTED: Validation passed when it should have failed')
except ValueError as e:
    print(f'Expected error caught: {e}')
except Exception as e:
    print(f'Unexpected error: {e}')
")
echo "  Result: $INVALID_INPUTS_RESULT"

if [[ $VALID_INPUTS_RESULT == *"Validation successful"* && $INVALID_INPUTS_RESULT == *"Expected error caught"* ]]; then
    echo "Status: PASS - Factory input validation working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Factory input validation not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

# Test 3: Factory Interface Definition
echo "Test 3: Factory Interface and Configuration"
echo "Expected: Factory interface defines complete contracts and configuration works properly"
echo "Executing:"

echo "  Testing factory configuration creation:"
FACTORY_CONFIG_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import FactoryConfig
try:
    config = FactoryConfig(
        factory_type='context',
        environment='testing',
        debug_mode=True,
        timeout=45,
        factory_config={'test': 'value'}
    )
    print(f'Config created successfully')
    print(f'Factory type: {config.factory_type}')
    print(f'Environment: {config.environment}')
    print(f'Debug mode: {config.debug_mode}')
    print(f'Timeout: {config.timeout}')
    print(f'Config keys: {list(config.factory_config.keys())}')
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $FACTORY_CONFIG_RESULT"

echo "  Testing abstract factory interface implementation:"
ABSTRACT_FACTORY_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import AbstractContextFactory, FactoryConfig

class TestFactory(AbstractContextFactory):
    def create_context(self, config):
        return {'context_type': 'test', 'environment': config.environment}
    
    def validate_config(self, config):
        self._validate_common_config(config)
        return True

try:
    factory = TestFactory('test_factory')
    config = FactoryConfig(factory_type='context', environment='testing')
    
    print(f'Factory created: {factory.factory_type}')
    print(f'Supports testing env: {factory.supports_environment(\"testing\")}')
    print(f'Config validation: {factory.validate_config(config)}')
    
    context = factory.create_context(config)
    print(f'Context created: {context}')
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $ABSTRACT_FACTORY_RESULT"

if [[ $FACTORY_CONFIG_RESULT == *"Config created successfully"* && $ABSTRACT_FACTORY_RESULT == *"Context created"* ]]; then
    echo "Status: PASS - Factory interface definition working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Factory interface definition not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

# Test 4: Factory Registry Functionality
echo "Test 4: Factory Registry Management"
echo "Expected: Registry manages multiple factories correctly and provides appropriate error handling"
echo "Executing:"

echo "  Testing factory registry operations:"
REGISTRY_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import FactoryRegistry, AbstractContextFactory, FactoryConfig

class TestFactory(AbstractContextFactory):
    def create_context(self, config):
        return {'type': self.factory_type, 'env': config.environment}
    def validate_config(self, config):
        return True

try:
    registry = FactoryRegistry()
    factory1 = TestFactory('cli_factory')
    factory2 = TestFactory('test_factory')
    
    # Register factories
    registry.register_factory('context', 'cli', factory1)
    registry.register_factory('context', 'testing', factory2)
    
    print(f'Factories registered successfully')
    
    # List available factories
    available = registry.list_available_factories()
    print(f'Available factories: {available}')
    
    # Retrieve and test factories
    cli_factory = registry.get_factory('context', 'cli')
    test_factory = registry.get_factory('context', 'testing')
    
    print(f'CLI factory retrieved: {cli_factory.factory_type}')
    print(f'Test factory retrieved: {test_factory.factory_type}')
    
    # Test context creation
    cli_config = FactoryConfig(factory_type='context', environment='cli')
    cli_context = cli_factory.create_context(cli_config)
    print(f'CLI context: {cli_context}')
    
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $REGISTRY_RESULT"

echo "  Testing registry error handling:"
REGISTRY_ERROR_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import FactoryRegistry, FactoryInterfaceError

try:
    registry = FactoryRegistry()
    
    # Try to get non-existent factory
    try:
        registry.get_factory('nonexistent', 'cli')
        print('UNEXPECTED: Should have raised error for nonexistent factory')
    except FactoryInterfaceError as e:
        print(f'Expected error for nonexistent factory: {type(e).__name__}')
    
    print('Error handling working correctly')
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $REGISTRY_ERROR_RESULT"

if [[ $REGISTRY_RESULT == *"CLI context"* && $REGISTRY_ERROR_RESULT == *"Expected error"* ]]; then
    echo "Status: PASS - Factory registry functionality working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Factory registry functionality not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

# Test 5: Cross-Environment Factory Support
echo "Test 5: Cross-Environment Factory Support"
echo "Expected: Factory interface supports both CLI and testing environments with proper isolation"
echo "Executing:"

echo "  Testing environment-specific factory behavior:"
CROSS_ENV_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import AbstractContextFactory, FactoryConfig, FactoryRegistry

class EnvironmentSpecificFactory(AbstractContextFactory):
    def __init__(self, factory_type, supported_env):
        super().__init__(factory_type)
        self.supported_env = supported_env
    
    def create_context(self, config):
        return {
            'factory_type': self.factory_type,
            'environment': config.environment,
            'supported': self.supports_environment(config.environment)
        }
    
    def validate_config(self, config):
        self._validate_common_config(config)
        return self.supports_environment(config.environment)
    
    def supports_environment(self, environment):
        return environment == self.supported_env

try:
    # Create environment-specific factories
    cli_factory = EnvironmentSpecificFactory('cli_factory', 'cli')
    testing_factory = EnvironmentSpecificFactory('testing_factory', 'testing')
    
    print(f'CLI factory supports CLI: {cli_factory.supports_environment(\"cli\")}')
    print(f'CLI factory supports testing: {cli_factory.supports_environment(\"testing\")}')
    print(f'Testing factory supports testing: {testing_factory.supports_environment(\"testing\")}')
    print(f'Testing factory supports CLI: {testing_factory.supports_environment(\"cli\")}')
    
    # Test with appropriate environments
    cli_config = FactoryConfig(factory_type='context', environment='cli')
    testing_config = FactoryConfig(factory_type='context', environment='testing')
    
    cli_context = cli_factory.create_context(cli_config)
    testing_context = testing_factory.create_context(testing_config)
    
    print(f'CLI context: {cli_context}')
    print(f'Testing context: {testing_context}')
    
    # Test validation
    print(f'CLI factory validates CLI config: {cli_factory.validate_config(cli_config)}')
    print(f'Testing factory validates testing config: {testing_factory.validate_config(testing_config)}')
    
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $CROSS_ENV_RESULT"

if [[ $CROSS_ENV_RESULT == *"CLI factory supports CLI: True"* && $CROSS_ENV_RESULT == *"Testing factory supports testing: True"* ]]; then
    echo "Status: PASS - Cross-environment factory support working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Cross-environment factory support not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

# Test 6: P1.1b Compatibility Testing
echo "Test 6: P1.1b SpecContext Compatibility"
echo "Expected: Factory interface supports patterns required for SpecContext creation"
echo "Executing:"

echo "  Testing SpecContext-compatible factory patterns:"
SPEC_CONTEXT_COMPAT_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import AbstractContextFactory, FactoryConfig
from spec_cli.utils.factory_utils import validate_factory_inputs

try:
    # Validate SpecContext-style inputs
    spec_inputs = validate_factory_inputs(
        factory_type='spec_context',
        timeout=30,
        debug_mode=True,
        factory_config={
            'project_root': '/test/project',
            'config_file': 'spec.config',
            'git_integration': True
        }
    )
    print(f'SpecContext inputs validated: {len(spec_inputs)} parameters')
    
    # Create SpecContext-compatible config
    config = FactoryConfig(
        factory_type=spec_inputs['factory_type'],
        environment='testing',
        debug_mode=spec_inputs['debug_mode'],
        timeout=spec_inputs['timeout'],
        factory_config=spec_inputs['factory_config']
    )
    print(f'SpecContext config created: {config.factory_type}')
    
    # Real factory interface testing with actual data structures
    class RealSpecContextCompatibilityFactory(AbstractContextFactory):
        def create_context(self, config):
            # Real context creation using actual config data
            return {
                'context_id': f'real_context_{config.factory_type}',
                'project_root': config.factory_config.get('project_root'),
                'environment': config.environment,
                'git_integration': config.factory_config.get('git_integration', False),
                'debug_mode': config.debug_mode,
                'timeout': config.timeout,
                'creation_timestamp': '2025-07-05T10:45:00Z'
            }
        
        def validate_config(self, config):
            self._validate_common_config(config)
            # Real validation logic
            required_keys = ['project_root']
            has_required = all(key in config.factory_config for key in required_keys)
            return has_required and config.factory_type == 'spec_context'
    
    factory = RealSpecContextCompatibilityFactory('spec_context')
    print(f'Real factory created: {factory.factory_type}')
    
    # Test real validation and creation workflow
    is_valid = factory.validate_config(config)
    print(f'Config validation result: {is_valid}')
    
    if is_valid:
        context = factory.create_context(config)
        print(f'Real context created: {context[\"context_id\"]}')
        print(f'Project root: {context[\"project_root\"]}')
        print(f'Git integration: {context[\"git_integration\"]}')
        print(f'Environment: {context[\"environment\"]}')
        print(f'Debug mode: {context[\"debug_mode\"]}')
        print(f'Timeout: {context[\"timeout\"]}')
        print(f'Creation timestamp: {context[\"creation_timestamp\"]}')
    else:
        print('Validation failed - config does not meet requirements')
    
except Exception as e:
    print(f'ERROR: {e}')
")
echo "  Result: $SPEC_CONTEXT_COMPAT_RESULT"

if [[ $SPEC_CONTEXT_COMPAT_RESULT == *"Real context created"* && $SPEC_CONTEXT_COMPAT_RESULT == *"Git integration: True"* ]]; then
    echo "Status: PASS - P1.1b SpecContext compatibility working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - P1.1b SpecContext compatibility not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking that factory interface methods are properly defined..."

INTERFACE_COMPLETENESS_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.factory_interface import AbstractContextFactory, FactoryConfig, FactoryRegistry
import inspect

try:
    # Check AbstractContextFactory has required methods
    abstract_methods = inspect.getmembers(AbstractContextFactory, predicate=inspect.isfunction)
    method_names = [name for name, _ in abstract_methods]
    
    required_methods = ['create_context', 'validate_config', 'supports_environment']
    has_all_methods = all(method in method_names for method in required_methods)
    
    print(f'AbstractContextFactory methods: {method_names}')
    print(f'Has all required methods: {has_all_methods}')
    
    # Check FactoryConfig has required fields
    config_fields = FactoryConfig.__dataclass_fields__.keys()
    required_fields = ['factory_type', 'environment', 'debug_mode', 'timeout', 'factory_config']
    has_all_fields = all(field in config_fields for field in required_fields)
    
    print(f'FactoryConfig fields: {list(config_fields)}')
    print(f'Has all required fields: {has_all_fields}')
    
    # Check FactoryRegistry has required methods
    registry_methods = [name for name, _ in inspect.getmembers(FactoryRegistry, predicate=inspect.ismethod)]
    required_registry_methods = ['register_factory', 'get_factory', 'list_available_factories']
    has_all_registry_methods = all(method in registry_methods for method in required_registry_methods)
    
    print(f'FactoryRegistry methods: {registry_methods}')
    print(f'Has all required registry methods: {has_all_registry_methods}')
    
    print(f'Interface completeness: {has_all_methods and has_all_fields and has_all_registry_methods}')
    
except Exception as e:
    print(f'ERROR: {e}')
")
echo "Interface completeness check: $INTERFACE_COMPLETENESS_RESULT"

echo "Verification complete"
echo

# Performance validation
echo "Performance validation..."
echo "Measuring factory operations response time..."

PERFORMANCE_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
import time
from spec_cli.utils.factory_utils import detect_environment_type, validate_factory_inputs
from spec_cli.core.factory_interface import FactoryConfig, FactoryRegistry

try:
    # Measure environment detection
    start_time = time.time()
    for _ in range(100):
        detect_environment_type()
    env_detection_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Measure input validation
    start_time = time.time()
    for _ in range(100):
        validate_factory_inputs(factory_type='test', timeout=30)
    validation_time = (time.time() - start_time) * 1000
    
    # Measure config creation
    start_time = time.time()
    for _ in range(100):
        FactoryConfig(factory_type='test', environment='testing')
    config_creation_time = (time.time() - start_time) * 1000
    
    print(f'Environment detection (100 calls): {env_detection_time:.2f}ms')
    print(f'Input validation (100 calls): {validation_time:.2f}ms')
    print(f'Config creation (100 calls): {config_creation_time:.2f}ms')
    
    # All operations should be fast (< 100ms for 100 calls)
    performance_ok = all(t < 100 for t in [env_detection_time, validation_time, config_creation_time])
    print(f'Performance acceptable: {performance_ok}')
    
except Exception as e:
    print(f'ERROR: {e}')
")
echo "Performance results: $PERFORMANCE_RESULT"

# Cleanup phase
echo "Cleaning up..."
unset SPEC_ENV TESTING PYTHONPATH
echo "Cleanup complete"

# Initialize counters if not already set
PASSED_TESTS=${PASSED_TESTS:-0}
FAILED_TESTS=${FAILED_TESTS:-0}
TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS && $TOTAL_TESTS -gt 0 ]]; then
    echo "ALL MANUAL TESTS PASSED - Factory interface working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Factory interface needs investigation"
    exit 1
fi