# tools/blueberry_greeting.py
# A new tool created dynamically by tool_creator.

def get_meta():
    """
    Returns metadata describing the tool.
    """
    return {
        "name": "blueberry_greeting",
        "description": "A tool that outputs 'hello blueberry'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "A message to include in the output."
                }
            },
            "required": ["message"]
        }
    }

def run(tool_input):
    """
    The main function for the newly created tool.
    """
    # The tool's name is hardcoded here to ensure it's always available.
    tool_name = "blueberry_greeting"
    print(f"[blueberry_greeting] tool was executed with input: {tool_input}")
    
    message = tool_input.get('message', 'No message provided.')

    # Using simple string formatting for the return message.
    return {
        "status": "success",
        "message": "This is the " + tool_name + " tool. Your message was: " + message
    }