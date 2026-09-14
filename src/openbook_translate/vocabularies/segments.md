# OpenBook controlled vocabulary — segments

Version `0.3.0-draft`. A **segment** is a slice *inside a match*. Ids are
`segment:<sport>:<slice>`; the formal form is
`urn:openbook:segment:<sport>:<slice>`. Segments are used for live state
(“we are in the first half”) and for which slice a bet is on (“first-half
total”). They are never baked into a `market:*` id.

**Every sport has `full-time`**: the whole contest as graded, including any
overtime, extra time, or shootout rules the league’s `ruleset` states.
`regulation` is the same contest without those extensions, where the
distinction is priced.

A numbered pattern (`inning-<n>`, `set-<n>`) is one id family. Replace
`<n>` with a positive integer. Consumers MUST accept values in the family
even when `<n>` is outside the usual range (extra innings, a fifth set).

Catch-all: `segment:unknown:unknown`. Consumers MUST accept unrecognised
`segment:*` values. Additions go through `CONTRIBUTING.md`; ids are stable
once published.

For what a segment is in plain language, see
[`../docs/taxonomy.md`](../docs/taxonomy.md).

## Soccer — `sport:soccer`

| Id | Name | Description |
| --- | --- | --- |
| `segment:soccer:full-time` | Full time | The match as graded, including extra time and penalties when the ruleset says they count. |
| `segment:soccer:regulation` | Regulation | The two halves only (including stoppage time). Extra time and penalties are excluded. |
| `segment:soccer:1st-half` | First half | First period of regulation, including first-half stoppage time. Not extra time. |
| `segment:soccer:2nd-half` | Second half | Second period of regulation, including second-half stoppage time. Not extra time. |
| `segment:soccer:extra-time` | Extra time | The whole extra-time period as graded (both extra-time halves). Not penalties. |
| `segment:soccer:extra-time-1st-half` | Extra time — first half | First extra-time period only. |
| `segment:soccer:extra-time-2nd-half` | Extra time — second half | Second extra-time period only. |
| `segment:soccer:penalties` | Penalties | The penalty shoot-out after extra time (or as the ruleset orders it). |

## Futsal — `sport:futsal`

| Id | Name | Description |
| --- | --- | --- |
| `segment:futsal:full-time` | Full time | The match as graded, including extra time and penalties when they count. |
| `segment:futsal:regulation` | Regulation | The two halves only. |
| `segment:futsal:1st-half` | First half | First half, including stoppage. |
| `segment:futsal:2nd-half` | Second half | Second half, including stoppage. |
| `segment:futsal:extra-time` | Extra time | Extra time as graded. |
| `segment:futsal:penalties` | Penalties | Penalty shoot-out. |

## Basketball — `sport:basketball`

| Id | Name | Description |
| --- | --- | --- |
| `segment:basketball:full-time` | Full time | The game as graded, including overtime. |
| `segment:basketball:regulation` | Regulation | Four quarters (or two halves) without overtime. |
| `segment:basketball:1st-half` | First half | Quarters 1–2 (or the first half in a two-half ruleset). |
| `segment:basketball:2nd-half` | Second half | Quarters 3–4, excluding overtime. |
| `segment:basketball:1st-quarter` | First quarter | First quarter only. |
| `segment:basketball:2nd-quarter` | Second quarter | Second quarter only. |
| `segment:basketball:3rd-quarter` | Third quarter | Third quarter only. |
| `segment:basketball:4th-quarter` | Fourth quarter | Fourth quarter only, excluding overtime. |
| `segment:basketball:overtime` | Overtime | All overtime periods taken together. Numbered OT periods are `overtime-<n>` if a book prices them separately. |
| `segment:basketball:overtime-<n>` | Overtime n | The nth overtime period. |

## American football — `sport:american-football`

| Id | Name | Description |
| --- | --- | --- |
| `segment:american-football:full-time` | Full time | The game as graded, including overtime. |
| `segment:american-football:regulation` | Regulation | Four quarters without overtime. |
| `segment:american-football:1st-half` | First half | Quarters 1–2. |
| `segment:american-football:2nd-half` | Second half | Quarters 3–4, excluding overtime. |
| `segment:american-football:1st-quarter` | First quarter | First quarter only. |
| `segment:american-football:2nd-quarter` | Second quarter | Second quarter only. |
| `segment:american-football:3rd-quarter` | Third quarter | Third quarter only. |
| `segment:american-football:4th-quarter` | Fourth quarter | Fourth quarter only, excluding overtime. |
| `segment:american-football:overtime` | Overtime | Overtime as graded by the league ruleset. |

## Australian rules — `sport:australian-rules`

| Id | Name | Description |
| --- | --- | --- |
| `segment:australian-rules:full-time` | Full time | The match as graded, including extra time. |
| `segment:australian-rules:regulation` | Regulation | Four quarters without extra time. |
| `segment:australian-rules:1st-quarter` | First quarter | First quarter only. |
| `segment:australian-rules:2nd-quarter` | Second quarter | Second quarter only. |
| `segment:australian-rules:3rd-quarter` | Third quarter | Third quarter only. |
| `segment:australian-rules:4th-quarter` | Fourth quarter | Fourth quarter only. |
| `segment:australian-rules:1st-half` | First half | Quarters 1–2. |
| `segment:australian-rules:2nd-half` | Second half | Quarters 3–4. |
| `segment:australian-rules:extra-time` | Extra time | Extra time as graded. |

## Ice hockey — `sport:ice-hockey`

| Id | Name | Description |
| --- | --- | --- |
| `segment:ice-hockey:full-time` | Full time | The game as graded, including overtime and shootout when they count. |
| `segment:ice-hockey:regulation` | Regulation | Three periods (60 minutes plus stoppages as the ruleset times them), excluding OT and shootout. |
| `segment:ice-hockey:1st-period` | First period | First period only. |
| `segment:ice-hockey:2nd-period` | Second period | Second period only. |
| `segment:ice-hockey:3rd-period` | Third period | Third period only, excluding overtime. |
| `segment:ice-hockey:overtime` | Overtime | Overtime as graded, excluding the shootout. |
| `segment:ice-hockey:shootout` | Shootout | The shootout after overtime. |

## Baseball — `sport:baseball`

| Id | Name | Description |
| --- | --- | --- |
| `segment:baseball:full-time` | Full time | The game as graded, including extra innings. |
| `segment:baseball:1st-half` | First half (innings 1–5) | Innings 1 through 5 as a single slice (F5). |
| `segment:baseball:first-7-innings` | First seven innings | Innings 1 through 7 as a single slice (F7). |
| `segment:baseball:inning-<n>` | Inning n | One inning. n is 1–9 in regulation; extra innings continue the same family. |
| `segment:baseball:extra-innings` | Extra innings | All innings after the ninth, taken together. |

## Tennis — `sport:tennis`

| Id | Name | Description |
| --- | --- | --- |
| `segment:tennis:full-time` | Full time | The match as graded (best of three or five, including a match tie-break). |
| `segment:tennis:set-<n>` | Set n | One set. n is 1–5. |
| `segment:tennis:set-<n>-game-<m>` | Set n, game m | One game inside a set, for per-game markets. |
| `segment:tennis:tiebreak-<n>` | Tie-break of set n | The tie-break that decides set n (or the match tie-break, when that is set n). |

## Volleyball — `sport:volleyball`

| Id | Name | Description |
| --- | --- | --- |
| `segment:volleyball:full-time` | Full time | The match as graded (usually best of five). |
| `segment:volleyball:set-<n>` | Set n | One set. n is 1–5. |

## Beach volleyball — `sport:beach-volleyball`

| Id | Name | Description |
| --- | --- | --- |
| `segment:beach-volleyball:full-time` | Full time | The match as graded (usually best of three). |
| `segment:beach-volleyball:set-<n>` | Set n | One set. n is 1–3. |

## Table tennis — `sport:table-tennis`

| Id | Name | Description |
| --- | --- | --- |
| `segment:table-tennis:full-time` | Full time | The match as graded (usually best of five or seven). |
| `segment:table-tennis:set-<n>` | Set n | One set (game). n is 1–7. |

## Badminton — `sport:badminton`

| Id | Name | Description |
| --- | --- | --- |
| `segment:badminton:full-time` | Full time | The match as graded (usually best of three). |
| `segment:badminton:set-<n>` | Set n | One game. n is 1–3. |

## Handball — `sport:handball`

| Id | Name | Description |
| --- | --- | --- |
| `segment:handball:full-time` | Full time | The match as graded, including extra time and penalties when they count. |
| `segment:handball:regulation` | Regulation | The two halves only. |
| `segment:handball:1st-half` | First half | First half. |
| `segment:handball:2nd-half` | Second half | Second half. |
| `segment:handball:extra-time` | Extra time | Extra time as graded. |
| `segment:handball:penalties` | Penalties | Penalty throw-off. |

## Field hockey — `sport:field-hockey`

| Id | Name | Description |
| --- | --- | --- |
| `segment:field-hockey:full-time` | Full time | The match as graded, including extra time and shootout when they count. |
| `segment:field-hockey:regulation` | Regulation | Four quarters without extra time. |
| `segment:field-hockey:1st-quarter` | First quarter | First quarter. |
| `segment:field-hockey:2nd-quarter` | Second quarter | Second quarter. |
| `segment:field-hockey:3rd-quarter` | Third quarter | Third quarter. |
| `segment:field-hockey:4th-quarter` | Fourth quarter | Fourth quarter. |
| `segment:field-hockey:1st-half` | First half | Quarters 1–2. |
| `segment:field-hockey:2nd-half` | Second half | Quarters 3–4. |
| `segment:field-hockey:extra-time` | Extra time | Extra time as graded. |
| `segment:field-hockey:shootout` | Shootout | Penalty shoot-out. |

## Water polo — `sport:water-polo`

| Id | Name | Description |
| --- | --- | --- |
| `segment:water-polo:full-time` | Full time | The match as graded, including extra time and penalties when they count. |
| `segment:water-polo:regulation` | Regulation | Four quarters without extra time. |
| `segment:water-polo:1st-quarter` | First quarter | First quarter. |
| `segment:water-polo:2nd-quarter` | Second quarter | Second quarter. |
| `segment:water-polo:3rd-quarter` | Third quarter | Third quarter. |
| `segment:water-polo:4th-quarter` | Fourth quarter | Fourth quarter. |
| `segment:water-polo:extra-time` | Extra time | Extra time as graded. |
| `segment:water-polo:penalties` | Penalties | Penalty shoot-out. |

## Lacrosse — `sport:lacrosse`

| Id | Name | Description |
| --- | --- | --- |
| `segment:lacrosse:full-time` | Full time | The match as graded, including overtime. |
| `segment:lacrosse:regulation` | Regulation | Four quarters without overtime. |
| `segment:lacrosse:1st-quarter` | First quarter | First quarter. |
| `segment:lacrosse:2nd-quarter` | Second quarter | Second quarter. |
| `segment:lacrosse:3rd-quarter` | Third quarter | Third quarter. |
| `segment:lacrosse:4th-quarter` | Fourth quarter | Fourth quarter. |
| `segment:lacrosse:overtime` | Overtime | Overtime as graded. |

## MMA — `sport:mma`

| Id | Name | Description |
| --- | --- | --- |
| `segment:mma:full-time` | Full time | The bout as graded (all scheduled rounds, including a fifth in a championship). |
| `segment:mma:round-<n>` | Round n | One round. n is 1–5. |

## Boxing — `sport:boxing`

| Id | Name | Description |
| --- | --- | --- |
| `segment:boxing:full-time` | Full time | The bout as graded (all scheduled rounds). |
| `segment:boxing:round-<n>` | Round n | One round. n is 1–12. |

## Golf — `sport:golf`

A four-round stroke-play event is one fixture unless the book splits days
into fixtures. Front nine / back nine are always relative to a round when
`round-<n>` is also priced; on `full-time` they mean the tournament’s
opening nine and closing nine of the last round only if the book says so
in `ruleset`. Prefer pairing them with `round-<n>` via two markets.

| Id | Name | Description |
| --- | --- | --- |
| `segment:golf:full-time` | Full time | The event as graded (all scheduled rounds, including a play-off if the ruleset counts it). |
| `segment:golf:round-<n>` | Round n | One round. n is 1–4. |
| `segment:golf:front-9` | Front nine | Holes 1–9 of the round this market is on (or of the event, if offered on `full-time`). |
| `segment:golf:back-9` | Back nine | Holes 10–18 of that round. |
| `segment:golf:hole-<n>` | Hole n | One hole. n is 1–18. |

## Motorsport — `sport:motorsport`

Qualifying, sprint and race are **separate fixtures**, not segments of one
another. Segments below are slices *inside* one of those fixtures.

| Id | Name | Description |
| --- | --- | --- |
| `segment:motorsport:full-time` | Full time | The session as graded (the whole qualifying, sprint, or race). |
| `segment:motorsport:q1` | Q1 | First qualifying segment, inside a Qualifying fixture. |
| `segment:motorsport:q2` | Q2 | Second qualifying segment. |
| `segment:motorsport:q3` | Q3 | Third qualifying segment (pole shoot-out). |
| `segment:motorsport:first-lap` | First lap | Lap 1 of the race (or of the session). |
| `segment:motorsport:lap-<n>` | Lap n | One numbered lap. |

## Cricket — `sport:cricket`

| Id | Name | Description |
| --- | --- | --- |
| `segment:cricket:full-time` | Full time | The match as graded (all innings the format plays). |
| `segment:cricket:1st-innings` | First innings | First innings of the match (or of the side, as the book’s `ruleset` states). |
| `segment:cricket:2nd-innings` | Second innings | Second innings. |
| `segment:cricket:3rd-innings` | Third innings | Third innings (Test cricket). |
| `segment:cricket:4th-innings` | Fourth innings | Fourth innings (Test cricket). |
| `segment:cricket:over-<n>` | Over n | One numbered over. |
| `segment:cricket:powerplay` | Powerplay | The fielding restriction block as the format defines it. |

## Rugby union — `sport:rugby-union`

| Id | Name | Description |
| --- | --- | --- |
| `segment:rugby-union:full-time` | Full time | The match as graded, including extra time when it counts. |
| `segment:rugby-union:regulation` | Regulation | The two halves only. |
| `segment:rugby-union:1st-half` | First half | First half, including stoppage. |
| `segment:rugby-union:2nd-half` | Second half | Second half, including stoppage. |
| `segment:rugby-union:extra-time` | Extra time | Extra time as graded. |

## Rugby league — `sport:rugby-league`

| Id | Name | Description |
| --- | --- | --- |
| `segment:rugby-league:full-time` | Full time | The match as graded, including extra time when it counts. |
| `segment:rugby-league:regulation` | Regulation | The two halves only. |
| `segment:rugby-league:1st-half` | First half | First half, including stoppage. |
| `segment:rugby-league:2nd-half` | Second half | Second half, including stoppage. |
| `segment:rugby-league:extra-time` | Extra time | Extra time as graded. |

## Snooker — `sport:snooker`

| Id | Name | Description |
| --- | --- | --- |
| `segment:snooker:full-time` | Full time | The match as graded (all scheduled frames). |
| `segment:snooker:frame-<n>` | Frame n | One frame. |

## Darts — `sport:darts`

| Id | Name | Description |
| --- | --- | --- |
| `segment:darts:full-time` | Full time | The match as graded (all scheduled sets). |
| `segment:darts:set-<n>` | Set n | One set. |
| `segment:darts:leg-<n>` | Leg n | One leg when the match is legs-only, or a running leg count the book prices as a slice. |
| `segment:darts:set-<n>-leg-<m>` | Set n, leg m | One leg inside a set. |

## Athletics — `sport:athletics`

Heats and a final of the same discipline on the same day may still be
separate fixtures. Use these slices when one fixture covers the round.

| Id | Name | Description |
| --- | --- | --- |
| `segment:athletics:full-time` | Full time | The result as graded for this fixture (the heat, the semi, or the final). |
| `segment:athletics:final` | Final | The final round when the fixture still names inner slices. |
| `segment:athletics:heat-<n>` | Heat n | One heat. |
| `segment:athletics:semi-final-<n>` | Semi-final n | One semi-final. |
| `segment:athletics:attempt-<n>` | Attempt n | One jump or throw. |
| `segment:athletics:lap-<n>` | Lap n | One numbered lap on the track. |

## Swimming — `sport:swimming`

| Id | Name | Description |
| --- | --- | --- |
| `segment:swimming:full-time` | Full time | The result as graded for this fixture. |
| `segment:swimming:heat-<n>` | Heat n | One heat. |
| `segment:swimming:semi-final-<n>` | Semi-final n | One semi-final. |
| `segment:swimming:final` | Final | The final when the fixture names inner slices. |

## Cycling — `sport:cycling`

A stage of a stage-race is a **fixture**. Slices below are inside one
stage or one one-day race.

| Id | Name | Description |
| --- | --- | --- |
| `segment:cycling:full-time` | Full time | The stage or race as graded. |
| `segment:cycling:lap-<n>` | Lap n | One numbered lap (criterium, track). |

## Skiing — `sport:skiing`

| Id | Name | Description |
| --- | --- | --- |
| `segment:skiing:full-time` | Full time | The run or combined result as graded. |
| `segment:skiing:run-<n>` | Run n | One numbered run (slalom, giant slalom). |

## Esports — `sport:esports`

A map or game is a slice of one match fixture, not a new match.

| Id | Name | Description |
| --- | --- | --- |
| `segment:esports:full-time` | Full time | The match as graded (all maps or games). |
| `segment:esports:map-<n>` | Map n | One map. n follows the series length (1–5, 1–7, …). |
| `segment:esports:game-<n>` | Game n | One game when the title uses “game” rather than “map”. |

## Unknown

| Id | Name | Description |
| --- | --- | --- |
| `segment:unknown:unknown` | Unknown | Catch-all (Q34) when the sport or the slice is not in this list. |
