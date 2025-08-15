# tools/read_file_content_tool.py
import os
import glob
from pathlib import Path
from typing import Dict, Any, List

def get_meta():
    return {
        'name': 'read_file_content_tool',
        'description': 'Reads the content of a file from a given path. Supports ~, env vars, relative paths, and simple globs.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'The path to the file to read. Supports ~, $ENV_VARS, ../, and globs like *.md'}
            },
            'required': ['path']
        }
    }

def _expand_user(p: str) -> str:
    """
    Robust ~ expansion:
      - ~ or ~/... using $HOME, $USERPROFILE, or pwd (POSIX)
      - ~username on POSIX (pwd)
    """
    p = p.strip().strip('"').strip("'")
    if not p.startswith('~'):
        return p

    # Handle "~" and "~/...":
    if p == '~' or p.startswith('~/'):
        home = os.environ.get('HOME') or os.environ.get('USERPROFILE')
        if not home:
            try:
                import pwd  # POSIX only
                home = pwd.getpwuid(os.getuid()).pw_dir
            except Exception:
                home = None
        if home:
            return home + p[1:]
        # As a last resort, let pathlib try
        return str(Path(p).expanduser())

    # Handle "~username"
    if os.name != 'nt':  # Windows has no pwd users
        try:
            import pwd
            user = p[1:].split('/', 1)[0]
            rest = p[1+len(user):]  # keep leading slash if present
            home = pwd.getpwnam(user).pw_dir
            return home + rest
        except Exception:
            pass

    return str(Path(p).expanduser())

def _expand_path(p: str) -> str:
    # Expand ~ first (our robust handler), then env vars, then normalize
    p = _expand_user(p)
    p = os.path.expandvars(p)
    return os.path.normpath(p)

def _glob_candidates(p: str) -> List[str]:
    # If the path contains glob chars, return matches (files only). Else return [p].
    if any(ch in p for ch in ['*', '?', '[']):
        return [m for m in glob.glob(p) if os.path.isfile(m)]
    return [p]

def run(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    raw_path = tool_input.get('path')
    if not raw_path or not isinstance(raw_path, str):
        return {'status': 'error', 'message': 'File path is required as a string.'}

    try:
        expanded = _expand_path(raw_path)
        candidates = _glob_candidates(expanded)

        if not candidates:
            return {'status': 'error', 'message': f'No files match path: {raw_path} (expanded: {expanded})'}

        if len(candidates) > 1:
            return {
                'status': 'error',
                'message': f'Ambiguous path matched multiple files ({len(candidates)}).',
                'matches': sorted(str(Path(c).resolve()) for c in candidates)[:50]
            }

        candidate = candidates[0]
        try:
            resolved = Path(candidate).resolve(strict=True)
        except FileNotFoundError:
            return {'status': 'error', 'message': f'File not found at path: {raw_path} (expanded: {candidate})'}

        if not resolved.is_file():
            return {'status': 'error', 'message': f'Path is not a file: {resolved}'}

        try:
            content = resolved.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return {'status': 'error', 'message': f'Failed to decode as UTF-8: {resolved}'}

        return {'status': 'success', 'resolved_path': str(resolved), 'markdown': content}

    except Exception as e:
        return {'status': 'error', 'message': f'Failed to read file for path {raw_path}: {e.__class__.__name__}: {e}'}

