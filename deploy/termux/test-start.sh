#!/data/data/com.termux/files/usr/bin/bash
set -eu
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
test_root="$(mktemp -d)"
printf '%s\n' "$test_root"
if [ ! -f "$script_dir/ensure-process.sh" ]; then
  printf 'FAIL: ensure-process.sh is not implemented\n' >&2
  exit 1
fi
. "$script_dir/ensure-process.sh"
test_pid=''
cleanup() {
  if [ -n "$test_pid" ]; then
    kill "$test_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT
test_pattern="^python3 -m http.server 18765 --bind 127\\.0\\.0\\.1 --directory $test_root$"
ensure_process "$test_pattern" "$test_root/service.log" "$test_root/service.pid" python3 -m http.server 18765 --bind 127.0.0.1 --directory "$test_root"
test_pid="$(cat "$test_root/service.pid")"
kill -0 "$test_pid"
ensure_process "$test_pattern" "$test_root/service.log" "$test_root/service.pid" python3 -m http.server 18765 --bind 127.0.0.1 --directory "$test_root"
test "$test_pid" = "$(cat "$test_root/service.pid")"
test "$(pgrep -f "$test_pattern" | wc -l)" -eq 1
printf 'PASS: absent process started; second call preserved one process\n'
