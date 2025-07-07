import sys

sys.path.insert(0, '/app')

from slice_2_3_function_restoration import FunctionRestorationSystem

# Test real system initialization
system = FunctionRestorationSystem()
print(f'System initialized with {len(system.stub_registry)} registry stubs')

# Test real analysis
missing_functions = ['test_validator', 'data_formatter']
test_requirements = {'context': 'component_test'}
analysis = system.analyze_missing_functions(missing_functions, test_requirements)
print(f'Analysis completed for {len(analysis)} functions')

# Test real restoration
signatures = {
    'test_validator': 'def test_validator(value: str) -> bool:',
    'data_formatter': 'def data_formatter(data: dict) -> str:'
}
restored = system.restore_missing_functions(signatures, analysis)
print(f'Restored {len(restored)} functions')

# Test real validation
validation = system.validate_restored_functions(restored)
print(f'Validation results: {validation}')

# Test actual function execution
validator = restored['test_validator']
validator_result = validator('test_input')
print(f'Validator function returned: {validator_result} (type: {type(validator_result)})')

formatter = restored['data_formatter']
formatter_result = formatter({'test': 'data'})
print(f'Formatter function returned: {formatter_result} (type: {type(formatter_result)})')

print('Component testing completed successfully')
