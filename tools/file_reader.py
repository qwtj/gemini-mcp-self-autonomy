# tools/file_reader.py
# An example of a dynamically loadable tool with self-describing metadata.

import os

def get_meta():
    """
    Returns metadata describing the tool for an AI to understand its purpose and usage.
    """
    return {
        "name": "file_reader",
        "description": "Reads the entire content of a specified file from the local filesystem. Useful for getting the content of text files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The relative or absolute path to the file to be read."
                }
            },
            "required": ["filepath"]
        }
    }

def run(tool_input):
    """
    The main function that the server will call.

    Args:
        tool_input (dict): A dictionary containing the input from the user's request.
                           This tool expects a 'filepath' key.

    Returns:
        dict: A dictionary containing the result of the tool's operation.
    """
    print(f"[file_reader] Received input: {tool_input}")

    filepath = tool_input.get('filepath')

    if not filepath:
        return {
            "status": "error",
            "message": "Input dictionary must contain a 'filepath' key."
        }

    # SECURITY NOTE: In a real application, you would need to strictly validate
    # this path to prevent directory traversal attacks.
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "status": "success",
                "filepath": filepath,
                "content": content
            }
        else:
            return {
                "status": "error",
                "message": f"File not found at path: {filepath}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred while reading the file: {str(e)}"
        }

