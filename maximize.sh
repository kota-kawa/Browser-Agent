#!/bin/bash
set -euo pipefail

/opt/bin/entry_point.sh "$@" &
ENTRYPOINT_PID=$!

sleep 2

maximize_chrome_windows() {
    local output window_id

    output="$(wmctrl -lx 2>/dev/null || true)"
    if [ -n "$output" ]; then
        while IFS= read -r line; do
            window_id="$(awk '{print $1}' <<< "$line")"
            [ -n "$window_id" ] || continue
            wmctrl -i -r "$window_id" -b add,maximized_vert,maximized_horz 2>/dev/null || true
        done <<< "$(awk 'tolower($4) ~ /(chrome|chromium)/ {print $0}' <<< "$output")"
        return 0
    fi

    output="$(wmctrl -l 2>/dev/null || true)"
    if [ -n "$output" ]; then
        while IFS= read -r line; do
            window_id="$(awk '{print $1}' <<< "$line")"
            [ -n "$window_id" ] || continue
            wmctrl -i -r "$window_id" -b add,maximized_vert,maximized_horz 2>/dev/null || true
        done <<< "$(awk 'tolower($0) ~ /chrome/ {print $0}' <<< "$output")"
    fi
}

# Keep polling while the Selenium entrypoint is alive so late-started Chrome
# windows (e.g., after the first session is created) are still maximized.
while kill -0 "$ENTRYPOINT_PID" 2>/dev/null; do
    maximize_chrome_windows
    sleep 1
done

wait "$ENTRYPOINT_PID"
