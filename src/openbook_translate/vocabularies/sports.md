# OpenBook controlled vocabulary — sports

Version `0.1.0-draft`. Each entry is a canonical `sport:*` id, a display
name, and what the id covers. Human map:
[`../docs/taxonomy.md`](../docs/taxonomy.md). Additions go through
[`../CONTRIBUTING.md`](../CONTRIBUTING.md); ids are stable and never
re-pointed once published.

A sport is the game being played, not a competition. The Olympics is a
league that contains many sports. Horse racing has no sport id in this
draft (`sport:unknown` if needed).

The default scoring unit is what a priced market counts when `basis` is
omitted (the sport or league `primaryUnit`). It is not a second id.

| Id | Name | Description |
| --- | --- | --- |
| `sport:soccer` | Soccer | Association football (11-a-side). Default unit: goals. Includes extra time and penalties as segments of the same fixture, not a different sport. |
| `sport:futsal` | Futsal | Indoor five-a-side football, its own sport (not soccer with a different league). Default unit: goals. |
| `sport:basketball` | Basketball | Five-a-side basketball as graded by the league ruleset. Default unit: points. |
| `sport:baseball` | Baseball | Baseball and the same scoring family (not softball as a separate id yet). Default unit: runs. |
| `sport:american-football` | American Football | Gridiron football as graded by the league ruleset. Default unit: points. |
| `sport:australian-rules` | Australian Rules | Australian rules football. Not rugby and not American football. Default unit: points. |
| `sport:ice-hockey` | Ice Hockey | Ice hockey as graded by the league ruleset. Default unit: goals. |
| `sport:tennis` | Tennis | Tennis, including singles and doubles as participant shape, not a different sport. Default unit: sets. Game and point totals use `basis`. |
| `sport:table-tennis` | Table Tennis | Table tennis (ping-pong). Default unit: sets. Point totals use `basis`. |
| `sport:volleyball` | Volleyball | Indoor volleyball. Default unit: sets. Point totals use `basis`. |
| `sport:beach-volleyball` | Beach Volleyball | Two-a-side sand volleyball. Not indoor volleyball. Default unit: sets. |
| `sport:badminton` | Badminton | Badminton, including singles and doubles. Default unit: sets. |
| `sport:handball` | Handball | Indoor team handball. Not Australian handball. Default unit: goals. |
| `sport:field-hockey` | Field Hockey | Field hockey (hockey on turf). Not ice hockey. Default unit: goals. |
| `sport:water-polo` | Water Polo | Water polo. Default unit: goals. |
| `sport:lacrosse` | Lacrosse | Field or box lacrosse as priced; the league ruleset says which. Default unit: goals. |
| `sport:golf` | Golf | Stroke-play and match-play golf. A round, a hole, or the tournament is a segment or an outright, not a different sport. Default unit: strokes. |
| `sport:mma` | Mixed Martial Arts | Mixed martial arts bouts. Default unit: rounds. Method of victory is a market type, not a sport. |
| `sport:boxing` | Boxing | Professional and amateur boxing. Default unit: rounds. |
| `sport:cricket` | Cricket | Cricket of any format (Test, ODI, T20). Format is the league/ruleset, not a sport id. Default unit: runs. Wickets and overs use `basis`. |
| `sport:rugby-union` | Rugby Union | Rugby union (15-a-side), including rugby sevens as the same sport with a different ruleset. Default unit: points. |
| `sport:rugby-league` | Rugby League | Rugby league (13-a-side). Not rugby union. Default unit: points. |
| `sport:snooker` | Snooker | Snooker. Frames are segments. Default unit: frames. |
| `sport:darts` | Darts | Darts. Sets and legs are segments. Default unit: sets. |
| `sport:athletics` | Athletics (track & field) | Track and field. Disciplines (100 m, marathon) hang beneath; they are not sports. Default unit: time or position, per discipline. |
| `sport:swimming` | Swimming | Pool swimming. Disciplines (100 m freestyle) hang beneath. Open-water is the same sport until a separate id is proposed. Default unit: time. |
| `sport:cycling` | Cycling | Road, track, and similar cycle racing as priced. A stage of a Grand Tour is a fixture, not a sport. Default unit: position or time. |
| `sport:motorsport` | Motorsport | Motor racing as priced (formula, prototype, touring, motorcycle). Series are leagues, not sports. Qualifying, sprint and race are fixtures. Default unit: position. |
| `sport:skiing` | Skiing | Alpine and related ski racing as priced. A discipline (downhill, slalom) hangs beneath when needed. Default unit: time. |
| `sport:esports` | Esports | Competitive video games as a sport family. Titles are disciplines beneath this id, not separate `sport:*` values, until a title is proposed as its own sport. Default unit: `other` (maps, rounds) — set `basis` on the market. |
| `sport:unknown` | Unknown | Catch-all when the sport is not in this list. Publishers SHOULD use this rather than inventing an id. Consumers MUST still accept unrecognised `sport:*` values. |

## Disciplines (sub-sport granularity)

Some sports carry disciplines beneath them. The id is readable
(`athletics:100m`), not an opaque code. A discipline is still the same
sport, sliced finer. A Games (the Olympics) is a **competition**, not a
sport: `league:athletics:INT:olympics` with a season per Games, and one
league per sport contested.

### Athletics

| Id | Event |
| --- | --- |
| `athletics:100m` | 100 metres |
| `athletics:110m-hurdles` | 110 metre hurdles |
| `athletics:long-jump` | Long jump |
| `athletics:high-jump` | High jump |
| `athletics:marathon` | Marathon |
| `athletics:decathlon` | Decathlon |
| `athletics:4x100m-relay` | 4 × 100 m relay |

### Swimming

| Id | Event |
| --- | --- |
| `swimming:100m-freestyle` | 100 metre freestyle |
| `swimming:200m-freestyle` | 200 metre freestyle |
| `swimming:100m-backstroke` | 100 metre backstroke |
| `swimming:100m-breaststroke` | 100 metre breaststroke |
| `swimming:100m-butterfly` | 100 metre butterfly |
| `swimming:200m-individual-medley` | 200 metre individual medley |
| `swimming:4x100m-freestyle-relay` | 4 × 100 m freestyle relay |

### Esports

A title is a discipline. The league is the circuit (Worlds, Major).

| Id | Title |
| --- | --- |
| `esports:league-of-legends` | League of Legends |
| `esports:counter-strike` | Counter-Strike |
| `esports:dota-2` | Dota 2 |
| `esports:valorant` | VALORANT |
| `esports:overwatch` | Overwatch |
| `esports:starcraft-2` | StarCraft II |
| `esports:rocket-league` | Rocket League |
