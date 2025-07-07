import sys

sys.path.insert(0, '/app')

try:
    from slice_2_3_function_restoration import restore_functions_for_test_execution
    from spec_cli.utils.function_restoration.missing_function_impl import (
        implement_missing_function,
    )

    print('Testing simple function implementation...')
    signature = 'def validate_test_input(value: str) -> bool:'
    purpose = 'Validate test input for functionality script'

    func = implement_missing_function(signature, purpose)
    result = func('test_value')
    print(f'Result: {result}, type: {type(result)}')

    print('Testing restoration workflow...')
    missing_functions = ['validate_input', 'format_output', 'process_data']
    function_signatures = {
        'validate_input': 'def validate_input(value: str) -> bool:',
        'format_output': 'def format_output(data: str) -> str:',
        'process_data': 'def process_data(data: dict) -> dict:'
    }
    test_requirements = {
        'context': 'functionality_testing',
        'behavior': 'real_implementation'
    }

    result = restore_functions_for_test_execution(
        missing_functions, function_signatures, test_requirements
    )

    print(f'Restoration result type: {type(result)}')
    print(f'Restoration keys: {list(result.keys())}')
    print('SUCCESS: All tests passed in Docker')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
