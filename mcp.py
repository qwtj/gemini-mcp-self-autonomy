#!/usr/bin/env python3

# server.py
# This script runs a simple web server that dynamically loads tools from a 'tools' directory.
# It can now also load newly created tools at runtime without a restart.

import os
import importlib.util
import traceback
import io
import contextlib
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Global Tool Registry ---
LOADED_TOOLS = {}

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

def execute_python_code(code_string):
    """
    Executes a string of Python code and captures its stdout output or any exceptions.
    This is treated as a built-in tool.

    SECURITY WARNING: Executing arbitrary code is extremely dangerous.
    This should ONLY be used in a sandboxed, secure environment.
    """
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(code_string, {})
        return True, output_buffer.getvalue()
    except Exception:
        return False, traceback.format_exc()

def load_single_tool(tool_name, tools_directory="tools"):
    """
    Loads or reloads a single, specified tool into the LOADED_TOOLS registry.
    This version is more robust and includes cache invalidation.
    """
    filename = f"{tool_name}.py"
    module_path = os.path.join(tools_directory, filename)

    print(f"--- Attempting to dynamically load '{tool_name}' ---")

    if not os.path.exists(module_path):
        print(f"  [!] FAILED: File does not exist at '{module_path}'")
        return False
    
    try:
        # Invalidate caches to ensure the import system sees the new file
        importlib.invalidate_caches()

        spec = importlib.util.spec_from_file_location(tool_name, module_path)
        if spec is None:
            print(f"  [!] FAILED: Could not create module spec for '{module_path}'")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "run") and callable(module.run):
            LOADED_TOOLS[tool_name] = module.run
            print(f"  [+] SUCCESS: Tool '{tool_name}' is now loaded and ready.")
            return True
        else:
            print(f"  [-] FAILED: Tool '{tool_name}' is missing a 'run' function.")
            return False
    except Exception:
        print(f"  [!] FAILED: An exception occurred while loading '{tool_name}':")
        print(traceback.format_exc())
        return False


def load_tools(tools_directory="tools"):
    """
    Scans a directory for Python files and registers them on startup.
    """
    print(f"--- Loading tools from '{tools_directory}' directory ---")
    if not os.path.isdir(tools_directory):
        print(f"Warning: Tools directory '{tools_directory}' not found.")
        return

    for filename in os.listdir(tools_directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            tool_name = filename[:-3]
            load_single_tool(tool_name, tools_directory)
    print("--- Tool loading complete ---")


@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """
    Handles requests for all tools and dynamically loads new tools created by tool_creator.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.get_json()
    if 'model' not in data or 'context' not in data:
        return jsonify({"status": "error", "message": "Payload must contain 'model' and 'context' keys"}), 400

    context_data = data['context']

    if 'tool_request' in context_data:
        tool_name = context_data['tool_request'].get('name')
        tool_input = context_data['tool_request'].get('input', {})

        if not tool_name:
            return jsonify({"status": "error", "message": "tool_request must specify a 'name'"}), 400

        print(f"Processing a '{tool_name}' tool request...")

        response_payload = {"status": "success"}
        status_code = 200

        try:
            tool_output = None
            if tool_name == 'python_executor':
                code_to_run = tool_input.get('code')
                if not code_to_run:
                    raise ValueError("No 'code' provided for python_executor tool")
                success, result = execute_python_code(code_to_run)
                tool_output = {"ran_successfully": success, "output": result}
            elif tool_name in LOADED_TOOLS:
                tool_function = LOADED_TOOLS[tool_name]
                tool_output = tool_function(tool_input)
            else:
                raise ValueError(f"Tool '{tool_name}' not found.")
            
            response_payload["tool_response"] = {
                "tool_name": tool_name, "output": tool_output
            }

            # --- DYNAMIC RELOAD LOGIC ---
            if tool_name == 'tool_creator' and tool_output.get('status') == 'success':
                new_tool_name = tool_output.get('created_tool_name')
                if new_tool_name:
                    load_single_tool(new_tool_name)

        except Exception as e:
            response_payload["status"] = "error"
            response_payload["tool_response"] = {
                "tool_name": tool_name, "output": str(e)
            }
            status_code = 400

        return jsonify(response_payload), status_code

    else:
        response_message = f"Hello World! Received context for model '{data['model']}'."
        return jsonify({"status": "success", "message": response_message}), 200


if __name__ == '__main__':
    load_tools()
    app.run(host='0.0.0.0', port=5000, debug=True)

