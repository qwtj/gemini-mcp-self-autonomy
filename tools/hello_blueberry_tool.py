# tools/hello_blueberry_tool.py
def get_meta():
    return {
        'name': 'hello_blueberry_tool',
        'description': 'A simple tool that outputs "hello blueberry".',
        'input_schema': { 'type': 'object', 'properties': {}, 'required': [] }
    }

def run(tool_input):
    return { 'status': 'success', 'message': 'hello blueberry' }