# tools/goodbye_cruel_world.py
# A simple tool that is similar to the hello_world tool.

def get_meta():
    """
    Returns metadata describing the tool for an AI to understand its purpose and usage.
    """
    return {
        "name": "goodbye_cruel_world",
        "description": "Prints a simple 'Goodbye Cruel World' message. Ignores all input.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

def run(tool_input):
    """
    The main function that the server will call for this tool.

    This tool ignores any input and simply returns a "Goodbye Cruel World"
    style message to confirm it was called successfully.

    Args:
        tool_input (dict): A dictionary containing the input from the user's request.
                           This tool does not use this input.

    Returns:
        dict: A dictionary containing the result of the tool's operation.
    """
    # You can print to the server's console for debugging purposes.
    print(f"[goodbye_cruel_world] tool was executed with input: {tool_input}")

    # The dictionary returned here will be sent back to the client
    # as the 'output' in the JSON response.
    return {
        "status": "success",
        "message": "Goodbye, cruel world, from the dynamically loaded tool!"
    }

