# MCP Web Client + Dynamic Tool Server (Gemini MCP Self Autonomy)

** The index.html is meant to be run within gemini.google.com for no config needed or api keys **
** The tools that use gemini all depend on API keys specifically the env var $GOOGLE_API_KEY **
** You can leverage my other repo ask and build a tool for it or look later I will make one **
** This app can built its own tools but mileage varies on your ability to prompt **

A tiny end-to-end demo that lets you:
- Discover available tools
- Use an LLM to plan a multi-step execution chain
- Execute tools via a local Flask server
- Dynamically create new tools at runtime (hot-reload)
- View a live execution log in the browser

This project consists of:
- A browser client (single HTML file) that plans and executes tool chains using Gemini.
- A Python Flask server that exposes a single /mcp endpoint and dynamically loads tools from a tools/ directory.

Important: This is a proof-of-concept. It executes arbitrary code. Do not expose it to untrusted input or run on machines containing sensitive data.

## Features

- Tool discovery via a meta tool (meta_tool_inspector)
- AI planning with Gemini 2.5 Flash (configurable)
- Dynamic tool creation (tool_creator) and hot-reload without server restarts
- Built-in python_executor that executes arbitrary Python (for demos only)
- Clean TailwindCSS UI and execution log

## Project Structure

- index.html — Web client with Tailwind UI and logic to:
  - Discover tools using meta_tool_inspector
  - Ask Gemini to generate a multi-step plan
  - Execute the plan step-by-step against the local server
  - Optionally ask Gemini to generate new tool code (tool_creator flow)
- server.py — Flask API server that:
  - Loads tools from tools/
  - Exposes POST /mcp to run tools or python code
  - Auto-loads newly created tools returned by tool_creator

You supply the tools/ directory with Python files defining tools.

## Prerequisites

- Python 3.9+
- pip
- A modern browser (Chrome, Edge, Firefox, Safari)
- Optional: Google Generative Language API key (Gemini) for planning and tool code generation

## Quick Start

1) Create and activate a virtual environment, install deps:
- python -m venv .venv
- source .venv/bin/activate  (Linux/macOS) or .venv\Scripts\activate (Windows)
- pip install flask flask-cors

2) Create a tools directory and add starter tools (see “Starter tools” below).

3) Start the server:
- python server.py
- The server listens on http://127.0.0.1:5000

4) Open the web client:
- Open index.html directly in your browser (double-click), or serve it via a simple static server.

5) Configure your Gemini API key (recommended):
- In index.html, set apiKey = "YOUR_API_KEY" in:
  - generateExecutionPlan()
  - generateToolCodeWithGemini()
- Or add your own planning logic if not using Gemini.

6) Enter a command and click “Run”.
- Example: write a python hello world script and save it to /tmp/hello.py

## How it Works

- The web client first calls meta_tool_inspector to list tools and their input schemas.
- It sends both the user command and the tool metadata to Gemini to generate a plan.
- The plan is a JSON array of steps like:
  - { "tool_name": "python_executor", "input": { "code": "..." } }
- Steps are executed one by one against /mcp.
- If a step uses tool_creator, the server writes a new tool file and hot-loads it for immediate use.
- If any step’s input depends on the previous step’s output, the client substitutes %%PREVIOUS_STEP_OUTPUT%% with that output.

## Security Warning

- The python_executor tool executes arbitrary Python code. This is extremely dangerous. Use it only in a sandboxed, disposable environment.
- Tools can perform file I/O, network calls, etc. Treat all requests as untrusted input. Do not run on production systems.

## Starter tools

Create a tools directory in the same folder as server.py, then add these files:

tools/meta_tool_inspector.py
```python
# tools/meta_tool_inspector.py
import os
import importlib.util
import json

def get_meta():
    return {
        "name": "meta_tool_inspector",
        "description": "Lists available tools and their metadata.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

def _load_tool_meta_from_file(module_name, module_path):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if not spec:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "get_meta") and callable(mod.get_meta):
            return mod.get_meta()
        else:
            # Minimal fallback if no get_meta is defined
            return {
                "name": module_name,
                "description": "No description provided.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
    except Exception:
        return None

def run(tool_input):
    tools_dir = os.path.join(os.path.dirname(__file__))
    available = []

    # Include built-in tools known by the server
    available.append({
        "name": "python_executor",
        "description": "Executes arbitrary Python code safely in-process (dangerous; demo only).",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": { "type": "string", "description": "Python code to execute" }
            },
            "required": ["code"]
        }
    })

    # tool_creator is expected to exist (or will be created)
    available.append({
        "name": "tool_creator",
        "description": "Creates a new tool file on disk and makes it available immediately.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": { "type": "string" },
                "tool_code": { "type": "string", "description": "Full Python source for the tool file" }
            },
            "required": ["tool_name", "tool_code"]
        }
    })

    # Discover other tools (excluding this file)
    for fname in os.listdir(tools_dir):
        if not fname.endswith(".py"):
            continue
        if fname.startswith("__"):
            continue
        module_name = fname[:-3]
        if module_name in ("meta_tool_inspector", "tool_creator"):
            continue
        meta = _load_tool_meta_from_file(module_name, os.path.join(tools_dir, fname))
        if meta:
            available.append(meta)

    return {
        "status": "success",
        "message": f"Discovered {len(available)} tools.",
        "available_tools": available
    }
```

tools/tool_creator.py
```python
# tools/tool_creator.py
import os
import re
from textwrap import dedent

TOOLS_DIR = os.path.dirname(__file__)

def get_meta():
    return {
        "name": "tool_creator",
        "description": "Creates a new Python tool file in the tools directory with a run() and optional get_meta().",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": { "type": "string", "description": "Snake_case Python identifier for the tool module" },
                "tool_code": { "type": "string", "description": "Full Python source for the tool" },
                "overwrite": { "type": "boolean", "description": "Overwrite existing tool file if true", "default": False }
            },
            "required": ["tool_name", "tool_code"]
        }
    }

def _is_valid_name(name: str) -> bool:
    return bool(re.match(r"^[a-z_][a-z0-9_]*$", name))

def run(tool_input):
    tool_name = tool_input.get("tool_name")
    tool_code = tool_input.get("tool_code")
    overwrite = bool(tool_input.get("overwrite", False))

    if not tool_name or not _is_valid_name(tool_name):
        return { "status": "error", "message": "Invalid tool_name. Use snake_case Python identifier." }

    if not tool_code or not isinstance(tool_code, str):
        return { "status": "error", "message": "tool_code must be a non-empty string." }

    path = os.path.join(TOOLS_DIR, f"{tool_name}.py")
    if os.path.exists(path) and not overwrite:
        return { "status": "error", "message": f"Tool '{tool_name}' already exists. Pass overwrite=true to replace it." }

    # Attempt to write the tool file
    code = dedent(tool_code)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return {
        "status": "success",
        "message": f"Created tool '{tool_name}' at {path}",
        "created_tool_name": tool_name
    }
```

Optional: A simple file_writer tool (useful for demos)
```python
# tools/file_writer.py
import os

def get_meta():
    return {
        "name": "file_writer",
        "description": "Writes text content to the given filesystem path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": { "type": "string" },
                "content": { "type": "string" },
                "make_parents": { "type": "boolean", "default": True }
            },
            "required": ["path", "content"]
        }
    }

def run(tool_input):
    path = tool_input["path"]
    content = tool_input["content"]
    make_parents = bool(tool_input.get("make_parents", True))

    parent = os.path.dirname(path) or "."
    if make_parents and parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "status": "success",
        "message": f"Wrote {len(content)} bytes to {path}",
        "output": path
    }
```

With these three tools, the planner can:
- Inspect tools
- Create new tools
- Write files to disk (either via file_writer or python_executor)

## Configuring Gemini

- Get an API key for the Google Generative Language API (Gemini).
- In index.html, set:
  - const apiKey = "YOUR_API_KEY";
  in both generateExecutionPlan and generateToolCodeWithGemini.
- Default model used: gemini-2.5-flash-preview-05-20
- The client expects the response as application/json and parses candidates[0].content.parts[0].text as JSON.

If you prefer not to use Gemini, you can:
- Replace generateExecutionPlan with a hardcoded plan generator.
- Replace generateToolCodeWithGemini with a local code template.

## Running

- Start the server: python server.py
- Open index.html in your browser
- Enter a command like:
  - write a python hello world script and save it to /tmp/hello.py
- Click Run and watch the execution log

Tip: On Windows, replace /tmp/hello.py with a valid Windows path like C:\Temp\hello.py.

## API: POST /mcp

Request (tool call)
```json
{
  "model": "web-client-agent-v1",
  "context": {
    "tool_request": {
      "name": "python_executor",
      "input": { "code": "print('hello')" }
    }
  }
}
```

Success response
```json
{
  "status": "success",
  "tool_response": {
    "tool_name": "python_executor",
    "output": {
      "ran_successfully": true,
      "output": "hello\n"
    }
  }
}
```

Error response (example)
```json
{
  "status": "error",
  "tool_response": {
    "tool_name": "some_tool",
    "output": "Tool 'some_tool' not found."
  }
}
```

Special behavior:
- When tool_name == "tool_creator" and the tool returns:
  - { "status": "success", "created_tool_name": "<name>" }
- The server immediately loads the new tool module (hot-reload).

## Writing Your Own Tools

- Each tool is a standalone Python module in tools/ named <tool_name>.py
- Must define:
  - get_meta() -> dict:
    - Keys: name, description, input_schema (JSON Schema object)
  - run(tool_input: dict) -> dict
- Return shape is flexible, but these keys are commonly used by the client for chaining/logging:
  - status: "success" | "error"
  - message: human-readable summary
  - output | content | generated_code: preferred outputs for chaining

Example skeleton
```python
def get_meta():
    return {
        "name": "my_tool",
        "description": "Does something useful.",
        "input_schema": {
            "type": "object",
            "properties": {
                "param": { "type": "string" }
            },
            "required": ["param"]
        }
    }

def run(tool_input):
    # your logic
    return {
        "status": "success",
        "message": "Ran my_tool",
        "output": "some result"
    }
```

Rules used by the client when chaining:
- If the previous step returns an object, the client tries generated_code, then content, then output, then message.
- To pass data from one step to the next, the plan uses the literal "%%PREVIOUS_STEP_OUTPUT%%" placeholder, which the client replaces at runtime.

## Troubleshooting

- “Tool 'X' not found”
  - Ensure tools/X.py exists and was loaded at server startup.
  - Check server console logs for load errors.
  - If X was created via tool_creator, confirm it returned created_tool_name and status: success.

- “Gemini API error while generating plan/code”
  - Set your API key in index.html.
  - Verify network access and API quota.
  - Make sure the model name is valid for your account/region.

- CORS or network issues
  - Server runs on http://127.0.0.1:5000; the client calls that exact URL.
  - Ensure nothing else is bound to that port.
  - Flask-CORS is enabled, so you should be able to open index.html locally.

- Auto-reload not working
  - tool_creator must return {"status": "success", "created_tool_name": "<name>"}.
  - The new file must contain a run() function (get_meta() is recommended).
  - Server logs will show success/failure of dynamic loading.

- File permissions / paths
  - Ensure the process has write permissions to the target path.
  - Use OS-appropriate paths; adjust examples accordingly.

## Notes and Limitations

- The planner relies on the meta tool’s output. Ensure your tools’ input_schema is accurate JSON Schema to help the planner.
- This is a local-only demo. No authentication, no sandboxing.
- The python_executor is convenient for demos but should never be exposed publicly.

## License

No license specified. Add one before sharing or using in other projects.
