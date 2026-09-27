#!/data/data/com.termux/files/usr/bin/bash

# Caller serializes startup with flock; never stops an existing process.
ensure_process() {
  local process_pattern="$1" process_log="$2" process_pid_file="$3"
  shift 3
  local process_pid process_attempt
  process_pid="$(pgrep -f "$process_pattern" | head -n 1)"
  if [ -n "$process_pid" ]; then
    printf '%s\n' "$process_pid" > "$process_pid_file"
    printf 'Already running: %s (PID %s)\n' "$1" "$process_pid"
    return 0
  fi
  nohup "$@" >> "$process_log" 2>&1 < /dev/null 9>&- &
  process_pid="$!"
  printf '%s\n' "$process_pid" > "$process_pid_file"
  for process_attempt in {1..30}; do
    if ! kill -0 "$process_pid" 2>/dev/null; then
      printf 'Startup failed: %s; see %s\n' "$1" "$process_log" >&2
      return 1
    fi
    if pgrep -f "$process_pattern" >/dev/null; then
      printf 'Started: %s (PID %s)\n' "$1" "$process_pid"
      return 0
    fi
    sleep 0.1
  done
  printf 'Startup not confirmed: %s; inspect %s\n' "$1" "$process_log" >&2
  return 1
}
