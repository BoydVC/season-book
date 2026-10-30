# Season Book: Fall 2026 yearbook + scorebook for Kid A and Kid B

**Live:** http://127.0.0.1:4246 (box only) · `/kida` and `/kidb` give the print layouts · `/api/season.json` returns the data
**Offline:** `dist/season-book-snapshot.html` is one self-contained file (~550 KB, fonts inlined, no network). It works from `file://` on any device.
**Print:** `dist/season-book-kida.pdf` · `dist/season-book-kidb.pdf`

A yearbook-style scorebook for the Aug 1 – Dec 31, 2026 fall season, built from Parent A's Google Calendar and Gmail. Both were read-only.

| Kid | Teams |
|---|---|
| **Kid A** (Kid A, b. 1/1/2015) | Team Alpha 12U soccer · Bravo 11u Blue baseball |
| **Kid B** (Kid B, b. 1/1/2013) | U14G Charlie (12/13 Charlie, Copa) soccer · *Delta 2031 Green lacrosse, also on her calendar, included as a bonus section* |

## What's in the book
- **Season at a glance:** a trading-card stat block per kid (games played, upcoming, travel venues, tournaments), plus results found, farthest trip, states, busiest weekend and practice count. Below it, a season ribbon with one row per team: ● played, ○ upcoming, × canceled, shaded bars for tournament days, and a "today" line.
- **Scorebook per team:** every game and scrimmage with date/time, opponent exactly as the calendar lists it, venue, field, town, straight-line miles from home, kit/uniform and arrival time when the event says so, and a **Result** column. Tournament weekends appear as ribbons. The next game is highlighted, canceled games are struck through, and the practices are summarized underneath.
- **Tournaments:** cards for each multi-game weekend, with its games and status.
- **Venues & drive notes:** a map-like plot of every venue town around Hometown with 25/50/100-mile rings. A nearest-first list gives each venue's heading and straight-line miles, plus any on-arrival directions, on-site spot notes and fields copied from the event descriptions.
- **Sources & honesty:** the calendars read and the Gmail searches run, with hit counts. It also has a log of 97 schedule-change emails (Google Calendar notifications for Bravo 11u and Delta) and the house rules.

## Honesty rules (enforced by tests)
- **Scores appear only when a source states them.** On Oct 7, 2026, five read-only Gmail searches turned up no team email or app notification giving a score for any of these teams. MaxPreps alerts in the inbox are for Nearby Town HS varsity, not the kids. So every played game says **result not found**.
  - To add a real score, put it in `data/results.json` as `{eventId, score, quote, source:{sender,date,messageId}}`. The quote must be the verbatim line containing the score. The message must also be in a saved Gmail page under `data/gmail/`. Then run `./run.sh all`.
- **Opponents are copied, never inferred.** The "vs" or "@" comes straight from the calendar title. It isn't a home/away claim. The WAGS championship slot shows "opponent TBD".
- **No ride coverage is assigned to anyone.** There are no drivers, carpools or legs in this book. Parent A and Parent B decide that.
- **Distances are town-level and straight-line.** Towns were geocoded once with OpenStreetMap Nominatim; only town names were sent. The cache is `data/geo.json`. Bel Air and Harwood were fixed to their ZIP centroids because the town search hit same-named places elsewhere. Drive times will be longer. "Travel venue" means 25 or more straight-line miles from Hometown.
- **Inferences are labeled:** "Venue 12 - Stadium" → Hometown (from the other Venue 2 events); "49 Venue Rd" → Timonium (the notes say a fairgrounds); "Loudoun, VA" tournament placeholder → Aldie (that's where its games are). The Alpha game on Oct 24 has no venue on the calendar and says so.

## Data sources (all read-only)
| Source | How | File |
|---|---|---|
| Team Alpha 12U calendar | `list_events` Aug 1 – Dec 31 | `data/raw/alpha.json` |
| 360Player U14G Charlie calendar | `list_events` | `data/raw/charlie.json` |
| Team-schedules calendar (TeamSnap: Bravo 11u, Delta 2031 Green) | `list_events` | `data/raw/teams.json` |
| Gmail (parent.a@example.com; alt-address forwards land here) | `search_threads` ×5 (+1 extra page) | `data/gmail/*.json`, `data/gmail_searches.json` |

`data/raw/family_events.json` was also pulled while scouting, but it's not used. The build reads only the three team calendars.
Calendar parsing follows Family Week's approach (`../family-week/ingest.py`: title/time/location, `[CANCELED]` handling, team prefixes). Family Week wasn't modified.

## Run / build / test
```bash
./run.sh all          # build data → render HTML → PDFs → screenshots → smoke test → (re)start server
./run.sh build        # python3 build.py && python3 render.py   (optional: ./run.sh build 2026-10-07T17:30:00-04:00 to pin "now")
./run.sh start|stop|restart|status   # 127.0.0.1:4246, setsid+nohup, pid in data/server.pid, log in data/server.log
./run.sh pdf          # dist/season-book-{kida,kidb}.pdf via headless Chrome
./run.sh shots        # screenshots/*.png (section crops from a full-page render)
python3 tests/smoke_test.py   # ~1,400 cross-checks
```
The smoke test checks:
- Every book event traces back to a raw calendar event with the same title, date and location.
- Every opponent is a substring of its source title.
- No team-calendar event in the season window is dropped.
- Results only come from sourced `results.json` entries.
- The team and kid stats add up.
- Miles recompute from `geo.json`.
- Played/upcoming status matches the build time.
- Every change-log row maps to a saved Gmail message.
- The snapshot is self-contained, renders in headless Chrome, shows "result not found" for each played game and has no ride-assignment text.
- Each PDF has the right kid and not the other kid's teams.
- The live server serves current data.

### Refreshing
Re-pull the three calendars with `list_events` (Aug 1 – Dec 31) into `data/raw/*.json` and re-run the Gmail searches in `data/gmail_searches.json`. Then run `./run.sh all`. Played/upcoming status is computed at build time.

## Files
`build.py` (classify, tournaments, venues, stats, Gmail log) · `venues.py` (venue/town parsing) · `geocode.py` (one-time town geocode) · `render.py` (inline HTML) · `server.py` · `run.sh` · `screenshot.sh` · `web/` (style.css, app.js, fonts) · `data/` · `dist/` · `screenshots/` · `tests/`


---
## Repo notes
- **Built:** Oct 2026 (TokenMax build week; see SHORTLIST/ledger), by TokenMax (Parent A's Grok Bot) on the Grok Bot box.
- **Run:** `./run.sh` (then open the localhost URL it prints).
- Imported from `/workspace/tokenmax/season-book` on Oct 23, 2026. node_modules, virtualenvs, logs and files over 20 MB were left out.
- Personal details (emails, phone numbers, home street address) were replaced with `[redacted-…]` placeholders.
