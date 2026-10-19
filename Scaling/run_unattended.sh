#!/usr/bin/env bash
# Run the pipeline unattended, e.g. overnight or over a weekend with the lid closed.
#
#   ./run_unattended.sh                        # everything
#   ./run_unattended.sh --context olympics     # any run_harness.py options
#
# It returns at once and keeps running after the editor and the terminal are closed.
# For as long as the run lasts it holds a systemd inhibitor that stops the laptop
# from sleeping, including when the lid is closed; when the run ends the inhibitor
# is released and the laptop sleeps normally again. No system setting is changed.
# It also starts the conexp-clj API that redraw needs if it is not already up, and
# stops it again afterwards.
#
#   tail -f logs/unattended.log                # progress
#   kill -- -"$(cat logs/unattended.pgid)"     # stop it
#
# After a stop, drawings still in progress finish or time out on their own within
# the budget; rerunning picks up where it left off, because every finished drawing
# and every recorded failure is saved as it happens.
#
# Needs mains power. With the lid closed and eight drawings at a time the laptop
# runs hot, so leave it on a hard surface; `--jobs 4` halves the load.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
mkdir -p logs

if [[ "${SCALING_DETACHED:-}" != 1 ]]; then
    SCALING_DETACHED=1 setsid nohup "$0" "$@" > logs/unattended.log 2>&1 < /dev/null &
    echo "started in the background; progress: tail -f logs/unattended.log"
    exit 0
fi

echo "$(ps -o pgid= $$ | tr -d ' ')" > logs/unattended.pgid
echo "started $(date '+%Y-%m-%d %H:%M'), options: ${*:-none}"

CONEXP_JAR="$(readlink -f ../../tools/conexp-clj.jar)"
started_conexp=""
if ! curl -s -m 3 -o /dev/null http://127.0.0.1:8080/; then
    # The API reads its console and exits at once if stdin is closed, hence the sleep.
    ( sleep infinity | java -jar "$CONEXP_JAR" --api --port 8080 > logs/conexp.log 2>&1 ) &
    started_conexp=$!
    for _ in $(seq 1 60); do
        curl -s -m 2 -o /dev/null http://127.0.0.1:8080/ && break
        sleep 2
    done
    echo "conexp API started for redraw"
fi

status=0
systemd-inhibit --what=sleep:idle:handle-lid-switch --mode=block \
    --who="scaling pipeline" --why="drawing sweep running (Scaling/run_unattended.sh)" \
    .venv/bin/python -u run_harness.py "$@" || status=$?

if [[ -n "$started_conexp" ]]; then
    pkill -P "$started_conexp" 2>/dev/null || true
    kill "$started_conexp" 2>/dev/null || true
fi
echo "finished $(date '+%Y-%m-%d %H:%M') with exit status $status; sleep allowed again"
rm -f logs/unattended.pgid
exit "$status"
