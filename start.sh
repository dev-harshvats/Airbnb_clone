#!/usr/bin/env bash
#
# Start the whole Airbnb clone locally: FastAPI backend (:8000) + Next.js frontend (:3000).
#
#   ./start.sh                 install what's missing, prepare the DB, start both servers
#   ./start.sh --skip-install  start without checking dependencies
#
# Works in Git Bash on Windows, macOS and Linux. Press Ctrl+C to stop both servers.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
SKIP_INSTALL=false

for arg in "$@"; do
  case "$arg" in
    --skip-install) SKIP_INSTALL=true ;;
    -h | --help) sed -n '3,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (try --help)" >&2; exit 1 ;;
  esac
done

info() { printf '\033[1;35m▸ %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31m✖ %s\033[0m\n' "$*" >&2; exit 1; }

is_windows() { [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]]; }

# --- prerequisites ---------------------------------------------------------

find_python() {
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
      "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      echo "$candidate"
      return
    fi
  done
  fail "Python 3.11+ is required (https://www.python.org/downloads/)"
}

command -v node >/dev/null 2>&1 || fail "Node.js 20+ is required (https://nodejs.org/)"
command -v npm >/dev/null 2>&1 || fail "npm is required (it ships with Node.js)"
PYTHON="$(find_python)"

if is_windows; then VENV_BIN="$BACKEND/.venv/Scripts"; else VENV_BIN="$BACKEND/.venv/bin"; fi

port_in_use() {
  (echo >"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
}
port_in_use "$BACKEND_PORT" && fail "Port $BACKEND_PORT is already in use (is the backend already running?)"
port_in_use "$FRONTEND_PORT" && fail "Port $FRONTEND_PORT is already in use (is the frontend already running?)"

# --- backend setup ---------------------------------------------------------

setup_backend() {
  cd "$BACKEND"
  if [[ ! -x "$VENV_BIN/python" && ! -x "$VENV_BIN/python.exe" ]]; then
    info "Creating Python virtual environment"
    "$PYTHON" -m venv .venv
  fi
  # Reinstall only when pyproject.toml changed since the last install.
  if [[ "$SKIP_INSTALL" == false && (! -f .venv/.installed || pyproject.toml -nt .venv/.installed) ]]; then
    info "Installing backend dependencies"
    "$VENV_BIN/python" -m pip install --quiet --upgrade pip
    "$VENV_BIN/python" -m pip install --quiet -e ".[dev]"
    touch .venv/.installed
  fi
  if [[ ! -f .env ]]; then
    info "Creating backend/.env from .env.example"
    cp .env.example .env
  fi
  if [[ -f alembic.ini ]]; then
    info "Applying database migrations"
    "$VENV_BIN/python" -m alembic upgrade head
  fi
  if [[ -d app/seed ]]; then
    info "Seeding demo data (skipped if already seeded)"
    "$VENV_BIN/python" -m app.seed
  fi
}

# --- frontend setup --------------------------------------------------------

setup_frontend() {
  cd "$FRONTEND"
  # Reinstall only when package-lock.json changed since the last install.
  if [[ "$SKIP_INSTALL" == false && (! -f node_modules/.package-lock.json || package-lock.json -nt node_modules/.package-lock.json) ]]; then
    info "Installing frontend dependencies"
    npm install --no-audit --no-fund
  fi
  if [[ ! -f .env.local ]]; then
    info "Creating frontend/.env.local from .env.example"
    cp .env.example .env.local
  fi
}

setup_backend
setup_frontend

# --- run both, stop both ---------------------------------------------------

PIDS=()

# All descendants of a process (children first), using the PID/PPID columns of `ps -ef`.
descendants() {
  local child
  for child in $(ps -ef | awk -v parent="$1" '$3 == parent { print $2 }'); do
    descendants "$child"
  done
  echo "$1"
}

stop_all() {
  trap - INT TERM EXIT
  echo
  info "Stopping servers"
  local pid tree=()
  for pid in "${PIDS[@]}"; do tree+=($(descendants "$pid")); done
  for pid in "${tree[@]}"; do
    if is_windows && [[ -r "/proc/$pid/winpid" ]]; then
      # Windows: kill each process with its native tree (uvicorn reloader, next workers).
      taskkill //F //T //PID "$(cat "/proc/$pid/winpid")" >/dev/null 2>&1 || true
    else
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}
trap stop_all INT TERM EXIT

prefix() {
  local label="$1" color="$2"
  while IFS= read -r line; do printf '\033[%sm[%s]\033[0m %s\n' "$color" "$label" "$line"; done
}

info "Starting backend on http://localhost:$BACKEND_PORT"
(cd "$BACKEND" && "$VENV_BIN/python" -m uvicorn app.main:create_app --factory --reload \
  --no-access-log --no-proxy-headers --host 127.0.0.1 --port "$BACKEND_PORT" 2>&1 | prefix api "1;34") &
PIDS+=($!)

info "Starting frontend on http://localhost:$FRONTEND_PORT"
(cd "$FRONTEND" && API_ORIGIN="http://localhost:$BACKEND_PORT" node_modules/.bin/next dev \
  --port "$FRONTEND_PORT" 2>&1 | prefix web "1;32") &
PIDS+=($!)

cat <<EOF

  App       http://localhost:$FRONTEND_PORT
  API docs  http://localhost:$BACKEND_PORT/api/docs

  Press Ctrl+C to stop.

EOF

# Exit (and stop the other server) as soon as either one dies.
# Polling instead of `wait -n` keeps this working on macOS's bash 3.2.
while kill -0 "${PIDS[0]}" 2>/dev/null && kill -0 "${PIDS[1]}" 2>/dev/null; do
  sleep 1
done
