#!/usr/bin/env bash
# Season Book: ./run.sh build|start|stop|restart|status|pdf|shots|test|all
set -e
cd "$(dirname "$0")"
PORT=4246; PIDF=data/server.pid; LOG=data/server.log
build(){ python3 build.py "$@" && python3 render.py; }
pdf(){
  for k in kida kidb; do
    P=$(mktemp -d /tmp/sb-pdf-XXXX)
    google-chrome --headless=new --user-data-dir="$P" --no-sandbox --disable-gpu --virtual-time-budget=5000 --run-all-compositor-stages-before-draw \
      --no-pdf-header-footer --print-to-pdf="dist/season-book-$k.pdf" "file://$PWD/dist/print-$k.html" >/dev/null 2>&1
    rm -rf "$P"; echo "dist/season-book-$k.pdf"
  done
}
shots(){ python3 tests/crop_shots.py; }
shots_old(){
  U="file://$PWD/dist/season-book-snapshot.html"
  ./screenshot.sh "$U" screenshots/01-overview.png 1440 1000
  ./screenshot.sh "$U" screenshots/02-full-book.png 1440 9000
  ./screenshot.sh "$U?kid=kida#kid-kida" screenshots/03-kida.png 1440 2600
  ./screenshot.sh "$U?kid=kidb#kid-kidb" screenshots/04-kidb.png 1440 2600
  python3 tests/crop_shots.py || true
}
start(){
  if status >/dev/null 2>&1; then echo "already running (pid $(cat $PIDF))"; return; fi
  setsid nohup python3 server.py >>"$LOG" 2>&1 < /dev/null & echo $! > "$PIDF"; sleep 0.8; status
}
stop(){ [ -f "$PIDF" ] && kill "$(cat $PIDF)" 2>/dev/null || true; rm -f "$PIDF"; echo stopped; }
status(){ if [ -f "$PIDF" ] && kill -0 "$(cat $PIDF)" 2>/dev/null && curl -sf "http://127.0.0.1:$PORT/healthz" >/dev/null; then echo "running on http://127.0.0.1:$PORT (pid $(cat $PIDF))"; else echo "not running"; return 1; fi; }
case "${1:-start}" in
  build) shift; build "$@";; start) start;; stop) stop;; restart) stop; start;; status) status;;
  pdf) pdf;; shots) shots;; test) python3 tests/smoke_test.py;;
  all) build; pdf; shots; python3 tests/smoke_test.py; stop; start;;
  *) echo "usage: $0 build|start|stop|restart|status|pdf|shots|test|all"; exit 2;;
esac
