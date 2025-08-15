# tools/tool_creator.py
# This tool's only job is to write a given string of code to a new tool file.

import os

def get_meta():
    """
    Returns metadata for the tool_creator itself.
    """
    return {
        "name": "tool_creator",
        "description": "Creates a new Python tool file from a given string of code. Use this to save a new, fully-formed tool to the filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "A valid python identifier for the new tool's name (e.g., 'my_new_tool'). This will be the filename without .py."
                },
                "tool_code": {
                    "type": "string",
                    "description": "A string containing the full, valid Python code for the new tool. Must include get_meta() and run() functions."
                }
            },
            "required": ["tool_name", "tool_code"]
        }
    }

def run(tool_input):
    """
    Writes the provided tool_code to a new .py file named after tool_name.
    """
    tool_name = tool_input.get('tool_name')
    tool_code = tool_input.get('tool_code')

    if not tool_name or not tool_code:
        return {
            "status": "error",
            "message": "Input must include both 'tool_name' and 'tool_code'."
        }

    if not tool_name.isidentifier():
        return {
            "status": "error",
            "message": f"'{tool_name}' is not a valid Python identifier. Please use letters, numbers, and underscores."
        }

    tools_directory = os.path.dirname(__file__)
    new_tool_path = os.path.join(tools_directory, f"{tool_name}.py")

    if os.path.exists(new_tool_path):
        return {
            "status": "error",
            "message": f"A tool named '{tool_name}' already exists at {new_tool_path}."
        }

    try:
        with open(new_tool_path, 'w', encoding='utf-8') as f:
            # Write the code exactly as provided by the AI
            f.write(tool_code.strip())

        # Return the name of the created tool for the server to load.
        return {
            "status": "success",
            "message": f"Successfully created and dynamically loaded new tool '{tool_name}'.",
            "created_tool_name": tool_name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create tool file: {str(e)}"
        }

