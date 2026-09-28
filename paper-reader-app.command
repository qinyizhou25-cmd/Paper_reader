#!/bin/sh
set -eu

fail() {
    status=$1
    shift
    printf 'Paper Reader: %s\n' "$*" >&2
    exit "$status"
}

usage() {
    printf '%s\n' 'Usage: paper-reader-app.command [options]

  --workspace PATH   Select an existing, initialized reading workspace.
  --host HOST        Bind address (default: 127.0.0.1).
  --port PORT        Listen port (default: 8765).
  --no-browser       Do not open a browser (--no-open is an alias).
  -h, --help         Show this help.

Runs in the repository directory, in the foreground; Ctrl+C stops the server.
Relative paths are relative to the repository. The Python backend reads .env.
Python selection: exported PAPER_READER_PYTHON, .venv/bin/python, then python3.
PAPER_READER_PYTHON must be one executable, not a command with arguments.
Python 3.10+ is required. Nothing is installed or initialized automatically.
For a new library, deliberately run paper_reader_agent.py --workspace PATH init.'
}

require_value() {
    if [ "$#" -lt 2 ] || [ -z "$2" ]; then
        fail 2 "$1 requires a nonempty value. Use --help for usage."
    fi
    case "$2" in
        --*) fail 2 "$1 requires a value before $2. Use --help for usage." ;;
    esac
}

workspace=
host=127.0.0.1
port=8765
open_browser=1
while [ "$#" -gt 0 ]; do
    case "$1" in
        --workspace|--host|--port)
            require_value "$@"
            case "$1" in
                --workspace) workspace=$2 ;;
                --host) host=$2 ;;
                --port) port=$2 ;;
            esac
            shift 2
            ;;
        --workspace=*|--host=*|--port=*)
            value=${1#*=}
            [ -n "$value" ] || fail 2 "${1%%=*} requires a nonempty value."
            case "$1" in
                --workspace=*) workspace=$value ;;
                --host=*) host=$value ;;
                --port=*) port=$value ;;
            esac
            shift
            ;;
        --no-browser|--no-open) open_browser=0; shift ;;
        -h|--help) usage; exit 0 ;;
        *) fail 2 "Unknown argument: $1. Use --help for usage." ;;
    esac
done

case "$0" in
    */*) launcher_path=$0 ;;
    *) launcher_path=$(command -v "$0") || fail 1 "Cannot locate this launcher." ;;
esac
case "$launcher_path" in
    /*) ;;
    *) launcher_path="$(pwd)/$launcher_path" ;;
esac
repo_dir=${launcher_path%/*}
CDPATH= cd "$repo_dir" || fail 1 "Cannot enter repository: $repo_dir"
repo_dir=$(pwd -P)

if [ -n "${PAPER_READER_PYTHON:-}" ]; then
    python=$PAPER_READER_PYTHON
elif [ -x "$repo_dir/.venv/bin/python" ]; then
    python=$repo_dir/.venv/bin/python
else
    python=python3
fi
if ! command -v "$python" >/dev/null 2>&1; then
    fail 127 "Python 3.10+ is required; executable not found or not executable: $python. Install Python, create this repository's .venv, or export PAPER_READER_PYTHON as one executable path."
fi

"$python" -c '
import sys
if sys.version_info < (3, 10):
    sys.stderr.write("Paper Reader requires Python 3.10+; found Python %s.\n" % sys.version.split()[0])
    sys.exit(1)
' || {
    status=$?
    printf 'Paper Reader: Python check failed for "%s". Use a working Python 3.10+ interpreter; recreate .venv or export PAPER_READER_PYTHON.\n' "$python" >&2
    exit "$status"
}

set -- serve --host "$host" --port "$port"
if [ -n "$workspace" ]; then
    set -- --workspace "$workspace" "$@"
fi
if [ "$open_browser" -eq 1 ]; then
    set -- "$@" --open
fi
exec "$python" "$repo_dir/paper_reader_agent.py" "$@"
