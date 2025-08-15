# tools/meta_tool_inspector.py
# This tool inspects all other tools in its directory and returns their metadata.

import os
import importlib.util
import traceback

def run(tool_input):
    """
    Scans the 'tools' directory for other Python scripts, imports them,
    and calls their get_meta() function to build a comprehensive list of available tools.

    Args:
        tool_input (dict): This tool does not require any input.

    Returns:
        dict: A dictionary containing a list of all discovered tool metadata.
    """
    tools_directory = os.path.dirname(__file__)
    available_tools = []

    print("[meta_tool_inspector] Starting tool discovery...")

    for filename in os.listdir(tools_directory):
        # Skip this file itself, private files, and non-python files
        if filename == os.path.basename(__file__) or not filename.endswith(".py") or filename.startswith("__"):
            continue

        tool_name = filename[:-3]
        module_path = os.path.join(tools_directory, filename)

        try:
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(tool_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check if the module has a 'get_meta' function
            if hasattr(module, "get_meta") and callable(module.get_meta):
                meta_info = module.get_meta()
                available_tools.append(meta_info)
                print(f"  [+] Found metadata for tool: '{tool_name}'")
            else:
                print(f"  [-] Warning: Tool '{tool_name}' has no get_meta() function.")

        except Exception:
            print(f"  [!] Error inspecting tool '{tool_name}': {traceback.format_exc()}")

    return {
        "status": "success",
        "available_tools": available_tools
    }

def get_meta():
    """
    Metadata for the inspector tool itself.
    """
    return {
        "name": "meta_tool_inspector",
        "description": "Inspects the tools directory and returns a list of all available tools, including their descriptions and required inputs. Use this to discover what tools you can use.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

