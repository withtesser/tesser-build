run_story_drafting() {
  cd "$ROOT/story-drafting" || return 1
  local ingress="${RESTATE_INGRESS:-http://localhost:38080}"
  local admin="${RESTATE_ADMIN:-http://localhost:39070}"
  local port="${STORY_DRAFTING_PORT:-9300}"
  local callback_host="${STORY_DRAFTING_CALLBACK_HOST:-host.docker.internal}"
  if [ -f .tesser-rendered ]; then
    local composition
    composition=$(head -n 1 .tesser-rendered)
    step "the tree matches $composition (srv.cli.render --check)"
    (cd "$ROOT/generator" && PYTHONPATH=.:../tesser-py python3 -m srv.cli.render --check "$ROOT/$composition" "$ROOT/story-drafting") || return 1
  fi
  step "tessercheck (zero findings over the whole tree)"
  tessercheck_tree "$PWD" || return 1
  local targets=()
  local d
  for d in */; do
    if [ -f "$d/__init__.py" ]; then targets+=("${d%/}"); fi
  done
  if [ -f conftest.py ]; then targets+=(conftest.py); fi
  if [ ${#targets[@]} -gt 0 ]; then
    step "mypy --strict"
    MYPYPATH=.:../tesser-py mypy --strict "${targets[@]}" || return 1
  fi
  step "pytest every tier but the root (no host served; Restate at $ingress)"
  RESTATE_INGRESS="$ingress" RESTATE_ADMIN="$admin" RESTATE_CALLBACK_HOST="$callback_host" \
    pytest -q --ignore=tests || return 1
  if [ ! -f srv/http/main.py ]; then
    step "pytest the root tier (no srv/http/main.py to serve)"
    pytest -q tests
    return
  fi
  step "serve srv.http.main on :$port and register its Restate endpoint at $admin"
  (exec env RESTATE_INGRESS="$ingress" PYTHONPATH=.:../tesser-py \
    python3 -m srv.http.main "0.0.0.0:$port") &
  local host=$!
  local registered=1
  for _ in $(seq 1 50); do
    if curl -sf -X POST "$admin/deployments" -H 'content-type: application/json' \
      -d "{\"uri\": \"http://$callback_host:$port/restate\", \"force\": true}" >/dev/null; then
      registered=0
      break
    fi
    sleep 0.2
  done
  if [ "$registered" -ne 0 ]; then
    echo "story-drafting: could not register http://$callback_host:$port/restate with $admin" >&2
    stop_host "$host" TERM
    return 1
  fi
  step "pytest the root tier (against the host on :$port, in STORY_DRAFTING_HOST)"
  STORY_DRAFTING_HOST="http://127.0.0.1:$port" pytest -q tests
  local status=$?
  stop_host "$host" INT
  return "$status"
}
