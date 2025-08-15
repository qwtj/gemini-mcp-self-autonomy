# tools/hello_world.py
# A very simple tool that demonstrates the dynamic loading functionality.

def get_meta():
    """
    Returns metadata describing the tool for an AI to understand its purpose and usage.
    """
    return {
        "name": "hello_world",
        "description": "Prints a simple 'Hello World' message. Ignores all input.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

def run(tool_input):
    """
    The main function that the server will call for this tool.

    This tool ignores any input and simply returns a "Hello World"
    style message to confirm it was called successfully.

    Args:
        tool_input (dict): A dictionary containing the input from the user's request.
                           This tool does not use this input.

    Returns:
        dict: A dictionary containing the result of the tool's operation.
    """
    # You can print to the server's console for debugging purposes.
    print(f"[hello_world] tool was executed with input: {tool_input}")

    # The dictionary returned here will be sent back to the client
    # as the 'output' in the JSON response.
    return {
        "status": "success",
        "message": "Hello from the dynamically loaded hello_world tool!"
    }

