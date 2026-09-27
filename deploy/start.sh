#!/data/data/com.termux/files/usr/bin/bash
set -eu
blog_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -f "$blog_root/server.pid" ]; then
  blog_pid="$(cat "$blog_root/server.pid")"
  if kill -0 "$blog_pid" 2>/dev/null; then
    printf 'Recorded process is still running (PID %s). Check it before restarting.\n' "$blog_pid"
    exit 1
  fi
fi
nohup python3 "$blog_root/serve.py" --directory "$blog_root/current" --port 8080 > "$blog_root/server.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$blog_root/server.pid"
printf 'Blog launched with PID %s. Check server.log and http://127.0.0.1:8080/.\n' "$!"
