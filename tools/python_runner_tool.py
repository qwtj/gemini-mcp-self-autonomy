# tools/python_runner_tool.py
import subprocess
import sys

def get_meta():
    """
    Returns the meta information of the tool as a dictionary.
    """
    return {
        "name": "python_runner_tool",
        "description": "Executes a python script from a file path and captures its output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "description": "The path to the python script file to execute."
                }
            },
            "required": ["script_path"]
        }
    }

def run(tool_input):
    """
    Executes a python script from a file in a separate process.

    Args:
        tool_input (dict): A dictionary containing the 'script_path'.

    Returns:
        dict: A dictionary containing the status and the script's output or error.
    """
    script_path = tool_input.get('script_path')
    if not script_path:
        return {"status": "error", "message": "Missing required input: script_path."}

    try:
        # Execute the script in a subprocess to capture stdout and stderr
        # This is safer than using exec() within the main server process.
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,  # This will raise an exception for non-zero exit codes
            timeout=30  # Add a timeout for safety
        )
        return {
            "status": "success",
            "output": result.stdout,
            "message": f"Script '{script_path}' executed successfully."
        }
    except FileNotFoundError:
        return {"status": "error", "message": f"Error: File not found at path: {script_path}"}
    except subprocess.CalledProcessError as e:
        # This catches errors within the script itself (non-zero exit code)
        return {
            "status": "error",
            "message": f"Error executing script '{script_path}'.",
            "stderr": e.stderr
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"Script '{script_path}' timed out after 30 seconds."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}
