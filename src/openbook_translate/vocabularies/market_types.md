# OpenBook controlled vocabulary — market types

Version `0.1.0-draft`. **This is the core contribution of OpenBook** — the
cross-book market taxonomy. Each entry is a canonical `market:*` id, its
shape, its category, the sides its outcomes take, and how it is graded.
Segments (`1st-half`, `inning-1`, …) are applied separately via
`segment` on the priced market, not baked into the market id. What the
market counts (goals, corners, maps) is `basis` on the priced market, not
a new `market:*` id.

For what these words mean without ids, see
[`../docs/taxonomy.md`](../docs/taxonomy.md).

**Shape** drives how a client renders and how a settlement grades:

| Shape | Means |
| --- | --- |
| `binary` | Two listed sides. No draw. |
| `n-way` | Three or more listed sides (or a field of participants). |
| `over-under` | `over` / `under` and a market `line`. |
| `handicap` | Two sides and a market `line` (including quarter-line Asian handicaps). |
| `exact-value` | One exact number (or small set of numbers) is the winning selection. |
| `correct-score` | Listed scores; leftover is `other`. |
| `yes-no` | `yes` / `no`. |
| `composite` | The market is a bundle of other market outcomes (parlay). It is not a single priced board. |

**Category** is the family on a `marketType` document (`main-line`,
`score-prop`, `game-prop`, `player-prop`, `outright`, `parlay-special`,
`same-game-parlay`). **Genre** is a free grouping label on that document
(`match`, `player`, `team`, `tournament`, `combination`).

A concrete priced selection is identified by
`(fixture, marketType, segment, line, side, basis)` — see the odds_change
schema.

This list is deliberately the set of kinds a mainstream book actually
prices. It grows through [`../CONTRIBUTING.md`](../CONTRIBUTING.md), with
stable ids. `market:unknown` is the catch-all (Q34). Consumers MUST accept
unrecognised `market:*` values.

## Main lines

| Id | Name | Shape | Category | Sides | Description |
| --- | --- | --- | --- | --- | --- |
| `market:moneyline` | Moneyline | n-way | main-line | home, away, (draw) | Who wins the segment as graded. Two-way when the sport has no draw; three-way when draw is a listed side. Not a handicap. |
| `market:spread` | Point Spread / Handicap | handicap | main-line | home, away | Who wins after the market `line` is applied to the score. Covers integer, half, and quarter (Asian) lines. A three-way handicap that lists draw is still this id; add `draw` as a side. |
| `market:total` | Total (Over/Under) | over-under | main-line | over, under | Combined score of both sides against the market `line`. `basis` says whether that is goals, points, corners, maps, … |
| `market:team-total` | Team Total | over-under | main-line | over, under | One participant’s score against the market `line`. The participant is the fixture’s home or away (or is named on the outcome). |
| `market:draw-no-bet` | Draw No Bet | binary | main-line | home, away | Who wins; a draw voids the bet. No `draw` side. |
| `market:double-chance` | Double Chance | n-way | main-line | home-or-draw, away-or-draw, home-or-away | Two of the three moneyline results, bundled. Graded on the same segment as a three-way moneyline. |

## Score props

| Id | Name | Shape | Category | Sides | Description |
| --- | --- | --- | --- | --- | --- |
| `market:correct-score` | Correct Score | correct-score | score-prop | homeTotal / awayTotal; leftover other | The exact final score of the segment. Each listed row carries both totals. Unlisted scores are `other`. No market `line`. |
| `market:exact-total` | Exact Total | exact-value | score-prop | participant (the number) or leftover other | The exact combined score. Each listed number is an outcome; unlisted remainder MAY be `other`. Not over/under. |
| `market:both-teams-to-score` | Both Teams To Score | yes-no | score-prop | yes, no | Whether both participants score at least once in the segment. |
| `market:clean-sheet` | Clean Sheet | yes-no | score-prop | yes, no | Whether the named side concedes zero. The side that must keep the sheet is home or away on the outcome (or `participant`). |
| `market:win-to-nil` | Win To Nil | binary | score-prop | home, away | Whether that side wins the segment without conceding. Not a clean sheet on a draw. |
| `market:odd-even-total` | Total Odd/Even | n-way | score-prop | odd, even | Parity of the combined score. Zero is even. |
| `market:winning-margin` | Winning Margin | n-way | score-prop | participant + outcome line or atLeast; leftover other | How far the winner wins by. Exact bands use outcome `line`; a plus-band (3 or more) uses `atLeast`. Leftover is `other`. No market `line`. |
| `market:highest-scoring-half` | Highest Scoring Half | n-way | score-prop | home, away, draw | Which half of regulation has more combined score. `home` is the first half, `away` the second; a tie is `draw`. |
| `market:race-to` | Race To (N) | binary | score-prop | home, away | Who first reaches the market `line` (points, goals, runs). If neither does, the book’s `ruleset` says void or a `none` row. |

## Game props

| Id | Name | Shape | Category | Sides | Description |
| --- | --- | --- | --- | --- | --- |
| `market:first-to-score` | First To Score | n-way | game-prop | home, away, none | Which side scores first in the segment. `none` is a listed selection (nobody scores), not leftover `other`. |
| `market:last-to-score` | Last To Score | n-way | game-prop | home, away, none | Which side scores last. `none` if the segment is 0–0. |
| `market:will-there-be-overtime` | Overtime Yes/No | yes-no | game-prop | yes, no | Whether the contest goes beyond regulation as the sport defines it (OT, extra time, extra innings). |
| `market:half-time-full-time` | Half-Time/Full-Time | n-way | game-prop | halfTime + fullTime (home, away, draw) | The regulation half-time result paired with the full-time result. Each row carries both. No market `line`. |
| `market:method-of-victory` | Method Of Victory | n-way | game-prop | participant | How the bout or match is decided (decision, KO/TKO, submission, points, and so on). Each listed method is an outcome. |
| `market:round-betting` | Round Betting | n-way | game-prop | participant (the round) | In which round the bout ends, or whether it goes the distance as a listed round. Goes-the-distance MAY instead be `market:will-there-be-overtime` when that mapping is honest; prefer this id for fight cards. |
| `market:to-qualify` | To Qualify | binary | game-prop | home, away | Which side advances from this fixture (two-leg tie, series game, qualifying heat). Not the tournament outright. |

## Player props

Player rows name `player` (the OpenBook player id). Over/under carries a
market `line`. Yes/no player boards omit market `line` and do not use
leftover `other`. `no` is optional on yes/no boards.

| Id | Name | Shape | Category | Sides | Description |
| --- | --- | --- | --- | --- | --- |
| `market:player-points` | Player Points | over-under | player-prop | over, under | One player’s points against the line. |
| `market:player-assists` | Player Assists | over-under | player-prop | over, under | One player’s assists. |
| `market:player-rebounds` | Player Rebounds | over-under | player-prop | over, under | One player’s rebounds. |
| `market:player-threes` | Player Three-Pointers | over-under | player-prop | over, under | One player’s made three-point field goals. |
| `market:player-blocks` | Player Blocks | over-under | player-prop | over, under | One player’s blocks. |
| `market:player-steals` | Player Steals | over-under | player-prop | over, under | One player’s steals. |
| `market:player-goals` | Player Goals | over-under | player-prop | over, under | One player’s goals (soccer, hockey, …). Anytime scorer is `market:player-anytime-scorer`, not this. |
| `market:player-shots-on-target` | Shots On Target | over-under | player-prop | over, under | One player’s shots on target. |
| `market:player-shots` | Player Shots | over-under | player-prop | over, under | One player’s shots (on or off target as the ruleset counts). |
| `market:player-passing-yards` | Passing Yards | over-under | player-prop | over, under | One player’s passing yards. |
| `market:player-rushing-yards` | Rushing Yards | over-under | player-prop | over, under | One player’s rushing yards. |
| `market:player-receiving-yards` | Receiving Yards | over-under | player-prop | over, under | One player’s receiving yards. |
| `market:player-touchdowns` | Player Touchdowns | over-under | player-prop | over, under | One player’s touchdowns scored (any kind unless `basis` narrows it). |
| `market:player-strikeouts` | Player Strikeouts | over-under | player-prop | over, under | Pitcher’s strikeouts, or batter’s, as `ruleset` / `basis` state. |
| `market:player-home-runs` | Player Home Runs | over-under | player-prop | over, under | One player’s home runs. |
| `market:player-runs` | Player Runs | over-under | player-prop | over, under | One batter’s runs, or one player’s runs in cricket, as the sport implies. |
| `market:player-wickets` | Player Wickets | over-under | player-prop | over, under | One bowler’s wickets. |
| `market:player-aces` | Player Aces | over-under | player-prop | over, under | One player’s aces (tennis). |
| `market:player-anytime-scorer` | Anytime Scorer | yes-no | player-prop | player + yes (no optional) | Whether that player scores at least once. No leftover `other`. No market `line`. |
| `market:player-first-scorer` | First Scorer | yes-no | player-prop | player + yes (no optional) | Whether that player scores the first score of the segment. Same row rules as anytime scorer. |
| `market:player-last-scorer` | Last Scorer | yes-no | player-prop | player + yes (no optional) | Whether that player scores the last score of the segment. |

## Outrights

Outrights sit on the competition (league / season / stage), not on one
match, unless the book still keys them to a fixture. Sides are
`participant` unless noted.

| Id | Name | Shape | Category | Sides | Description |
| --- | --- | --- | --- | --- | --- |
| `market:outright-winner` | Tournament / Outright Winner | n-way | outright | participant | Who wins the competition (or the season). |
| `market:to-make-final` | To Reach The Final | yes-no | outright | yes, no | Whether the named participant reaches the final. |
| `market:group-winner` | Group Winner | n-way | outright | participant | Who wins the named group (a `stage`). |
| `market:to-qualify-from-group` | To Qualify From Group | yes-no | outright | yes, no | Whether the named participant leaves the group in a qualifying place. |
| `market:head-to-head` | Head To Head | binary | outright | home, away | Two named participants; who finishes ahead in the event (golf, motorsport, tournament placing). Not the match moneyline. |
| `market:podium` | Podium | yes-no | outright | yes, no | Whether the named participant finishes in the top three. |
| `market:top-n` | Top N | yes-no | outright | yes, no | Whether the named participant finishes in the top N. N is the market `line` (4 means top four). |

## Combinations

| Id | Name | Shape | Category | Sides | Description |
| --- | --- | --- | --- | --- | --- |
| `market:same-game-parlay` | Same-Game Parlay | composite | same-game-parlay | references other market outcomes | A bundle of legs from one fixture. Each leg points at another market outcome. Not a new shape of moneyline. |
| `market:parlay` | Parlay / Accumulator | composite | parlay-special | cross-fixture legs | A bundle of legs from more than one fixture. Same `composite` shape as same-game parlay; the difference is whether legs share a fixture. |
| `market:unknown` | Unknown | — | — | — | Catch-all (Q34). Publishers SHOULD use this rather than inventing an id. Consumers MUST accept unrecognised `market:*` values. |

### Notes

- A `handicap` market always has a `line`. An `over-under` always has
  `over` / `under` outcomes and a `line`. `n-way` enumerates listed
  outcomes. A yes/no player board names `player` on each row and omits
  market `line`.
- `composite` markets do not grade from a scoreboard row; they grade from
  the grades of their legs.
- `market:race-to` uses a market `line` for N even though it lives with the
  score props.
