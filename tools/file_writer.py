# tools/file_writer.py
# A tool that writes given content to a specified file.

import os
import re

def get_meta():
    """
    Returns metadata for the file_writer tool.
    """
    return {
        "name": "file_writer",
        "description": "Writes or overwrites a file with the provided content. Use this to save text, code, or any string data to a file on the local filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The absolute or relative path of the file to be written (e.g., '/tmp/hello.py' or 'output.txt')."
                },
                "content": {
                    "type": "string",
                    "description": "The string content to be written into the file. If the content contains a markdown code block, only the code will be extracted and written."
                }
            },
            "required": ["filepath", "content"]
        }
    }

def run(tool_input):
    """
    Writes the provided content to the specified filepath.
    If the content contains a python markdown block, it extracts the code first.
    """
    filepath = tool_input.get('filepath')
    content = tool_input.get('content')

    if filepath is None or content is None:
        return {
            "status": "error",
            "message": "Input must include both 'filepath' and 'content'."
        }

    # --- NEW LOGIC ---
    # Check for a python markdown block and extract the code if it exists.
    # This makes the tool more robust to verbose AI outputs.
    code_match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
    if code_match:
        print("[file_writer] Found python code block. Extracting code.")
        content_to_write = code_match.group(1).strip()
    else:
        # If no block is found, use the content as-is.
        content_to_write = content.strip()


    # SECURITY WARNING: In a real-world scenario, you would want to
    # heavily sanitize this filepath to prevent writing to sensitive system files.
    try:
        # Ensure the directory exists
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_to_write)

        return {
            "status": "success",
            "message": f"Successfully wrote {len(content_to_write)} characters to '{filepath}'."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to write to file: {str(e)}"
        }

