# tools/list_files_in_path.py
import os

def get_meta():
    return {
        "name": "list_files_in_path",
        "description": "Lists files and directories at a given path, expanding user and environment variables in the path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to list files from. Can include `~` for home directory or environment variables like `$HOME`."
                }
            },
            "required": ["path"]
        }
    }

def run(tool_input):
    path = tool_input.get("path")

    if not path:
        return {"status": "error", "message": "Path input is required."}

    try:
        # Expand user (~) and environment variables ($VAR) in the path
        expanded_path = os.path.expanduser(os.path.expandvars(path))

        if not os.path.exists(expanded_path):
            return {"status": "error", "message": f"Path does not exist: '{expanded_path}'"}

        if not os.path.isdir(expanded_path):
            return {"status": "error", "message": f"Path is not a directory: '{expanded_path}'"}

        files_and_dirs = os.listdir(expanded_path)
        return {"status": "success", "path": expanded_path, "contents": files_and_dirs}

    except PermissionError:
        return {"status": "error", "message": f"Permission denied to access path: '{expanded_path}'"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}