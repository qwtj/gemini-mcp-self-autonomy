# tools/print_numbers_tool.py
def get_meta():
    return {
        'name': 'print_numbers_tool',
        'description': 'A tool that prints numbers from 1 to 10.',
        'input_schema': { 'type': 'object', 'properties': {}, 'required': [] }
    }

def run(tool_input):
    numbers_list = []
    for i in range(1, 11):
        numbers_list.append(str(i))
    result_message = "Numbers from 1 to 10: " + ", ".join(numbers_list)
    return { 'status': 'success', 'message': result_message }