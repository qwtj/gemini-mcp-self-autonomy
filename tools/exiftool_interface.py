# tools/exiftool_interface.py
import subprocess
import json
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union

def get_meta():
    return {
        'name': 'exiftool_interface',
        'description': (
            "Interact with ExifTool for reading/writing metadata on image/media files. "
            "Supports ~, environment variables, relative paths, and globs. Requires ExifTool in PATH."
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'Path to the image/media file. Supports ~, $ENV_VARS, ../, and globs like *.jpg'
                },
                'operation': {
                    'type': 'string',
                    'enum': ['read', 'write'],
                    'description': 'Use "read" to extract metadata or "write" to update metadata.'
                },
                'tags_to_read': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Optional for "read": list of specific tags to extract (e.g., ["FileName","CreateDate"]).'
                },
                'metadata_to_write': {
                    'type': 'object',
                    'additionalProperties': {'type': 'string'},
                    'description': 'Optional for "write": dict of tag->string value pairs to write.'
                }
            },
            'required': ['file_path', 'operation']
        }
    }

# ---------- Path handling helpers ----------

def _expand_user(p: str) -> str:
    """
    Robust ~ and ~user expansion with fallbacks.
    """
    p = (p or "").strip().strip('"').strip("'")
    if not p.startswith('~'):
        return p

    # "~" or "~/" case
    if p == '~' or p.startswith('~/'):
        home = os.environ.get('HOME') or os.environ.get('USERPROFILE')
        if not home:
            try:
                import pwd
                home = pwd.getpwuid(os.getuid()).pw_dir
            except Exception:
                home = None
        return (home + p[1:]) if home else str(Path(p).expanduser())

    # "~username" on POSIX
    if os.name != 'nt':
        try:
            import pwd
            user = p[1:].split('/', 1)[0]
            rest = p[1 + len(user):]
            home = pwd.getpwnam(user).pw_dir
            return home + rest
        except Exception:
            pass

    return str(Path(p).expanduser())

def _expand_path(p: str) -> str:
    p = _expand_user(p)
    p = os.path.expandvars(p)
    return os.path.normpath(p)

def _glob_candidates(p: str) -> List[str]:
    # Return file matches if glob chars present; else return [p]
    if any(ch in p for ch in ['*', '?', '[']):
        return [m for m in glob.glob(p) if os.path.isfile(m)]
    return [p]

def _resolve_single_path(raw: str) -> Tuple[Union[str, None], Union[str, None], List[str]]:
    """
    Returns (resolved_path, error_message, matches_list_if_ambiguous)
    - resolved_path: absolute path string if exactly one file resolved, else None
    - error_message: error string or None
    - matches_list_if_ambiguous: list of absolute paths if multiple matches
    """
    expanded = _expand_path(raw)
    candidates = _glob_candidates(expanded)

    if not candidates:
        return None, f'No files match path: {raw} (expanded: {expanded})', []

    if len(candidates) > 1:
        matches = sorted(str(Path(c).resolve()) for c in candidates)[:200]
        return None, f'Ambiguous path matched multiple files ({len(candidates)}).', matches

    candidate = candidates[0]
    try:
        resolved = Path(candidate).resolve(strict=True)
    except FileNotFoundError:
        return None, f'File not found at path: {raw} (expanded: {candidate})', []

    if not resolved.is_file():
        return None, f'Path is not a file: {resolved}', []

    return str(resolved), None, []

# ---------- ExifTool availability ----------

def _check_exiftool() -> Union[None, str]:
    try:
        subprocess.run(['exiftool', '-ver'], check=True, capture_output=True, text=True, timeout=5)
        return None
    except FileNotFoundError:
        return 'ExifTool is not installed or not found in system PATH.'
    except subprocess.CalledProcessError as e:
        return f'ExifTool found but version check failed: {e.stderr.strip()}'
    except subprocess.TimeoutExpired:
        return 'ExifTool version check timed out.'
    except Exception as e:
        return f'Unexpected error during ExifTool check: {e}'

# ---------- Main tool API ----------

def run(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    file_path = tool_input.get('file_path')
    operation = tool_input.get('operation')
    tags_to_read = tool_input.get('tags_to_read', [])
    metadata_to_write = tool_input.get('metadata_to_write', {})

    if not isinstance(file_path, str) or not file_path.strip():
        return {'status': 'error', 'message': 'file_path is required as a non-empty string.'}
    if operation not in ('read', 'write'):
        return {'status': 'error', 'message': f'Invalid operation: "{operation}". Must be "read" or "write".'}

    resolved_path, err, matches = _resolve_single_path(file_path)
    if err:
        out = {'status': 'error', 'message': err}
        if matches:
            out['matches'] = matches
        return out

    avail_err = _check_exiftool()
    if avail_err:
        return {'status': 'error', 'message': avail_err}

    base_command = ['exiftool']

    if operation == 'read':
        command = base_command + ['-json', resolved_path]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, errors='ignore', timeout=300)
            output_data = json.loads(result.stdout) if result.stdout.strip() else []
            metadata: Dict[str, Any] = output_data[0] if output_data else {}

            if tags_to_read:
                # Only include requested tags that exist
                metadata = {tag: metadata.get(tag) for tag in tags_to_read if tag in metadata}

            # Return raw metadata as "data" (no vague message)
            return {
                'status': 'success',
                'resolved_path': resolved_path,
                'data': metadata
            }

        except json.JSONDecodeError as e:
            snippet = (result.stdout or '')[:500] if 'result' in locals() else 'N/A'
            return {'status': 'error', 'message': f'Failed to parse ExifTool JSON output: {e}. Output snippet: {snippet}'}
        except subprocess.CalledProcessError as e:
            return {'status': 'error', 'message': f'ExifTool read failed: {e.stderr.strip()}. Command: {" ".join(command)}'}
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': 'ExifTool read operation timed out.'}
        except Exception as e:
            return {'status': 'error', 'message': f'Unexpected error during read: {e}'}

    # operation == 'write'
    if not isinstance(metadata_to_write, dict) or not metadata_to_write:
        return {'status': 'error', 'message': 'metadata_to_write is required for "write" and must be a non-empty object.'}

    # Ensure all values are strings (per schema)
    write_args = []
    for tag, value in metadata_to_write.items():
        if not isinstance(value, str):
            return {'status': 'error', 'message': f'Invalid value type for "{tag}". Must be a string.'}
        write_args.append(f'-{tag}={value}')

    command = base_command + write_args + [resolved_path]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, errors='ignore', timeout=300)
        return {
            'status': 'success',
            'resolved_path': resolved_path,
            'data': json.loads(json.dumps({'summary': result.stdout.strip()}, indent=2))
        }
    except subprocess.CalledProcessError as e:
        return {'status': 'error', 'message': f'ExifTool write failed: {e.stderr.strip()}. Command: {" ".join(command)}'}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'message': 'ExifTool write operation timed out.'}
    except Exception as e:
        return {'status': 'error', 'message': f'Unexpected error during write: {e}'}

# ---------- Optional CLI for quick testing ----------
if __name__ == '__main__':
    import argparse, sys
    ap = argparse.ArgumentParser(description='exiftool_interface quick test')
    ap.add_argument('file_path', help='Path to file (supports ~, env vars, globs)')
    ap.add_argument('--op', choices=['read','write'], default='read')
    ap.add_argument('--tag', action='append', help='Tags to read (repeatable)')
    ap.add_argument('--set', action='append', help='For write: TAG=VALUE (repeatable)')
    args = ap.parse_args()

    tags = args.tag or []
    meta: Dict[str, str] = {}
    if args.set:
        for kv in args.set:
            if '=' not in kv:
                print(json.dumps({'status':'error','message':f'Invalid --set "{kv}". Use TAG=VALUE'}))
                sys.exit(2)
            k, v = kv.split('=', 1)
            meta[k] = v

    out = run({
        'file_path': args.file_path,
        'operation': args.op,
        'tags_to_read': tags,
        'metadata_to_write': meta
    })
    print(json.dumps(out, ensure_ascii=False))

