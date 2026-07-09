#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
cat > .venv/bin/alipin <<'WRAPPER'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" exec "$SCRIPT_DIR/python" -m alipin.cli "$@"
WRAPPER
chmod +x .venv/bin/alipin

echo "Alipin setup complete. Try: source .venv/bin/activate && alipin --help"
