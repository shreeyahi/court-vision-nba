# CourtVision NBA

### A roster-level forecast of the 2026–27 NBA season

Transactions are easy to list. Consequences are harder.

CourtVision asks what happens when every official move, projected player, aging curve, injury assumption, and minute of playing time has to fit inside the same league: 30 teams, 82 games each, and exactly 1,230 wins.

> Snapshot: July 15, 2026. The offseason is still moving. Reported and on-hold transactions remain outside the official forecast until finalized.

| 592 projected players | 60 incoming rookies | 11 seasons of player data | 20,000 simulated seasons |
|---:|---:|---:|---:|
| 240 minutes per team | 18 records changed from V1 | 4 current injury overrides | 18 passing tests |

---

## EAST 

| Seed | Team | Record | Chance to make ECF | Chance to win East |
|---:|---|---:|---:|---:|
| 1 | Detroit Pistons | **51–31** | 28.5% | 14.9% |
| 2 | Cleveland Cavaliers | **49–33** | 23.4% | 12.4% |
| 3 | New York Knicks | **48–34** | 21.0% | 10.6% |
| 4 | Charlotte Hornets | **47–35** | 18.6% | 9.0% |
| 5 | Boston Celtics | **46–36** | 17.2% | 8.5% |
| 6 | Orlando Magic | **45–37** | 15.4% | 7.5% |
| 7 | Philadelphia 76ers | **45–37** | 15.1% | 7.5% |
| 8 | Miami Heat | **45–37** | 15.6% | 7.4% |
| 9 | Toronto Raptors | **45–37** | 15.5% | 7.6% |
| 10 | Atlanta Hawks | **43–39** | 12.6% | 6.3% |
| 11 | Chicago Bulls | **35–47** | 5.4% | 2.7% |
| 12 | Milwaukee Bucks | **32–50** | 3.8% | 1.8% |
| 13 | Washington Wizards | **29–53** | 2.8% | 1.4% |
| 14 | Brooklyn Nets | **28–54** | 2.6% | 1.2% |
| 15 | Indiana Pacers | **28–54** | 2.6% | 1.1% |

### Detroit, not New York is the model’s East favorite.

Detroit owns the highest projected record and the highest probability of reaching the Finals from the East. The model sees a 54-win historical baseline, then applies a −4.08-win full-roster adjustment. After league-wide recentering, that becomes 51–31.

The leading projected Detroit values are Jalen Duren at +3.48 wins above replacement and Cade Cunningham at +3.40.

If the question is whether New York should be favored because of Jalen Brunson, CourtVision’s answer is no. Brunson still projects as a star—25.28 PPG and +2.83 wins above replacement—but New York’s complete future roster is worth 1.91 fewer wins than the roster already embedded in its 49-win baseline. The Knicks finish third at 48–34, with a 10.6% chance of winning the East.

### Why is Philly only seventh after acquiring Jaylen Brown?

Because CourtVision does not award a headline-trade bonus.

| Philadelphia input | Model value |
|---|---:|
| Historical baseline | 44 wins |
| Old roster value | 9.02 |
| New roster value | 9.18 |
| Net roster adjustment | **+0.16 wins** |
| Raw forecast | 44.16 wins |
| Published record | **45–37** |

Jaylen Brown projects at 24.76 PPG and +2.59 wins above replacement. But the transaction ledger also sends Paul George to Boston, while Philadelphia’s other departures include Kelly Oubre Jr., Quentin Grimes, and Andre Drummond. Brown is part of a complete roster replacement calculation, not an isolated addition.

The largest constraint is availability. Joel Embiid projects at 25.03 PPG and +1.63 wins above replacement, but his base availability is only 32.4% from the recent-history model. That suppresses his season-level value even though his per-game projection remains elite.

This is a model answer, not a claim that Philadelphia lacks talent. Maxey, Brown, Embiid, and VJ Edgecombe are the team’s four largest projected contributors. The point is that star names do not bypass age, availability, departures, or the 240-minute limit.

### Charlotte after LaMelo: the best honesty test in the project

Charlotte is fourth in V2—not third.

| Charlotte input | Model value |
|---|---:|
| Historical baseline | 48 wins |
| Full-roster adjustment | **−2.01 wins** |
| Raw forecast | 45.99 wins |
| Published record | **47–35** |

The LaMelo Ball trade does hurt Charlotte. The model simply does not send the Hornets to the bottom because it also sees:

| Player | Projected PPG | Projected value |
|---|---:|---:|
| Kon Knueppel | 19.71 | +2.24 wins |
| Miles Bridges | 17.75 | +1.61 |
| Naz Reid | 13.68 | +1.31 |
| Ryan Kalkbrenner | 8.38 | +1.11 |
| Coby White | 18.72 | +0.98 |
| Brandon Miller | 20.42 | +0.93 |

But there is a real blind spot here: CourtVision does not know that LaMelo’s playmaking created open looks for Knueppel. Kon’s sophomore projection is based on his own production, role, and historical sophomore development—not on an on/off or teammate-dependency model.

If Kon’s efficiency materially depended on LaMelo, Charlotte may be too high. That is not something the current code can rule out.

---

## WEST 

| Seed | Team | Record | Chance to make WCF | Chance to win West |
|---:|---|---:|---:|---:|
| 1 | Oklahoma City Thunder | **54–28** | 34.5% | 18.5% |
| 2 | San Antonio Spurs | **54–28** | 35.1% | 18.3% |
| 3 | Houston Rockets | **49–33** | 21.9% | 10.5% |
| 4 | Denver Nuggets | **49–33** | 21.8% | 10.7% |
| 5 | Los Angeles Lakers | **47–35** | 17.6% | 8.7% |
| 6 | Minnesota Timberwolves | **45–37** | 15.1% | 7.7% |
| 7 | Portland Trail Blazers | **43–39** | 11.6% | 5.5% |
| 8 | Phoenix Suns | **42–40** | 10.8% | 5.2% |
| 9 | Golden State Warriors | **38–44** | 7.1% | 3.3% |
| 10 | LA Clippers | **38–44** | 7.0% | 3.2% |
| 11 | New Orleans Pelicans | **34–48** | 4.5% | 2.2% |
| 12 | Dallas Mavericks | **34–48** | 4.6% | 2.1% |
| 13 | Utah Jazz | **30–52** | 2.8% | 1.4% |
| 14 | Memphis Grizzlies | **29–53** | 2.9% | 1.5% |
| 15 | Sacramento Kings | **28–54** | 2.5% | 1.2% |

OKC and San Antonio round to the same record, but the simulator does not treat them as identical. San Antonio has the slightly higher WCF probability; OKC has the slightly higher championship probability, 9.8% to 9.6%.

The West is also where current injury uncertainty is visible in the standings:

| Team | Base roster adjustment | Injury downside | Injury upside |
|---|---:|---:|---:|
| Golden State | −0.65 wins | −0.50 | +0.48 |
| Dallas | +1.70 wins | −0.50 | +0.31 |

Golden State’s range comes from Jimmy Butler III and Moses Moody. Dallas’s comes from Kyrie Irving and Dereck Lively II.

---

## V1 → V2 // WHAT ACTUALLY MOVED

Revision 2 changed the published record of 18 teams. The remaining 12 can still have different decimal roster values that disappear when the league is recentered and rounded to whole wins.

### East changes

| Team | V1 | V2 | Difference |
|---|---:|---:|---:|
| Detroit | 53–29 | 51–31 | −2 |
| Cleveland | 46–36 | 49–33 | +3 |
| New York | 49–33 | 48–34 | −1 |
| Boston | 47–35 | 46–36 | −1 |
| Atlanta | 46–36 | 43–39 | −3 |
| Chicago | 36–46 | 35–47 | −1 |
| Milwaukee | 31–51 | 32–50 | +1 |
| Washington | 28–54 | 29–53 | +1 |
| Indiana | 26–56 | 28–54 | +2 |

### West changes

| Team | V1 | V2 | Difference |
|---|---:|---:|---:|
| San Antonio | 57–25 | 54–28 | −3 |
| Denver | 48–34 | 49–33 | +1 |
| Los Angeles Lakers | 45–37 | 47–35 | +2 |
| Minnesota | 43–39 | 45–37 | +2 |
| Phoenix | 44–38 | 42–40 | −2 |
| LA Clippers | 40–42 | 38–44 | −2 |
| Dallas | 33–49 | 34–48 | +1 |
| Utah | 29–53 | 30–52 | +1 |
| Sacramento | 27–55 | 28–54 | +1 |

---

## QUESTIONS THE MODEL HAS TO EARN

### 1. How is NCAA talent translated into an NBA projection?

**Not from NCAA box scores.**

CourtVision currently uses draft position as a compressed proxy for college production, scouting, age, competition, and team evaluation. The path is:

    NCAA and international evidence
                ↓
       NBA team draft decision
                ↓
          overall pick bucket
                ↓
    historical NBA rookie outcomes

The code groups picks into 1–3, 4–10, 11–20, 21–30, second round, and undrafted/international. It then learns rookie PIE, playing time, scoring rate, and availability from the 2015–2025 draft classes.

| Draft bucket | PIE prior | MPG prior | Points/36 prior | Availability |
|---|---:|---:|---:|---:|
| Picks 1–3 | .0894 | 21.04 | 16.30 | 61.9% |
| Picks 4–10 | .0756 | 20.69 | 14.05 | 70.3% |
| Picks 11–20 | .0735 | 15.85 | 13.67 | 58.0% |
| Picks 21–30 | .0736 | 13.70 | 13.21 | 49.9% |
| Second round | .0643 | 8.73 | 12.15 | 30.3% |

The estimates are shrunk toward the overall rookie mean so one unusually strong historical class cannot dominate the forecast.

**Proof in code:** [draft buckets](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L89-L105) · [rookie-prior training](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L405-L486) · [2026 rookie ledger](data/manual/rookies_2026.csv)

What this does not do is distinguish two prospects selected in the same bucket using their individual NCAA efficiency, competition level, position, or age. That is a V3 feature, not a hidden V2 claim.

### 2. How are rookies accounted for?

There are two different groups that are easy to mix up:

| Player group | 2026–27 treatment |
|---|---|
| Players drafted in 2025, including Cooper Flagg and Kon Knueppel | Sophomore model using real 2025–26 NBA statistics |
| Players drafted in 2026 | Rookie prior based on historical draft bucket |

Incoming top-three rookies such as Darryn Peterson, AJ Dybantsa, and Cameron Boozer receive a conservative 9.53-PPG prior and roughly +0.24 to +0.25 wins above replacement after team-minute allocation.

Summer League receives zero weight. A few exhibition games are not treated as NBA evidence.

### 3. How are sophomore and third-year players projected?

Career stage is defined for the season being forecast:

| Completed NBA seasons before 2026–27 | Forecast group |
|---:|---|
| 0 | Rookie |
| 1 | Sophomore |
| 2 | Third-year |
| 3 or more | Veteran age band |

The model pairs consecutive historical player seasons and learns the next-year change in four targets. Extreme changes are clipped, and group estimates are shrunk toward the league mean.

| Forecast group | Δ PIE | Δ MPG | Δ Points/36 | Δ Availability |
|---|---:|---:|---:|---:|
| Sophomore | +.00516 | +1.035 | +.667 | +.0195 |
| Third-year | +.00403 | +.471 | +.574 | −.0236 |

Cooper Flagg therefore enters 2026–27 as a sophomore:

| Player | Age | Group | PPG | Availability | Projected value |
|---|---:|---|---:|---:|---:|
| Cooper Flagg | 20 | Sophomore | 22.29 | 87.3% | +2.42 wins |
| Kon Knueppel | 21 | Sophomore | 19.71 | 100.0% | +2.24 |
| Stephon Castle | 22 | Third-year | 16.72 | 86.2% | +1.26 |
| Alex Sarr | 22 | Third-year | 15.84 | 64.4% | +0.99 |

**Proof in code:** [career-stage labels](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L108-L130) · [season pairing](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L270-L309) · [development curves](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L312-L340) · [published curves](reports/development_curves_2026_27.csv)

### 4. How does age change a player?

Sophomores and third-year players use career stage first. Veterans use their age during the forecast season. That avoids giving a young player both a career-stage bonus and a separate youth bonus.

| Forecast-age group | Δ PIE | Δ MPG | Δ Points/36 | Δ Availability |
|---|---:|---:|---:|---:|
| 24 and under | +.00141 | +.265 | +.222 | −.0365 |
| 25–27 | −.00047 | −.199 | +.009 | −.0405 |
| 28–30 | −.00294 | −1.182 | −.253 | −.0614 |
| 31–33 | −.00468 | −1.885 | −.493 | −.0713 |
| 34–36 | −.00550 | −2.402 | −.726 | −.0701 |
| 37+ | −.00484 | −2.199 | −.402 | −.0841 |

Paul George is the cleanest example. The 2026–27 projection treats him as 37, not as Oklahoma City-era Paul George:

| Player | Age | Group | MPG | Points/36 | PPG | Availability | Value |
|---|---:|---|---:|---:|---:|---:|---:|
| Paul George | 37 | Veteran 37+ | 29.51 | 19.75 | 16.19 | 44.9% | +0.90 wins |

Player baselines weight 2023–24 at 15%, 2024–25 at 30%, and 2025–26 at 55% before the age or career-stage change is added.

**Proof in code:** [recent-season weights](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L53-L73) · [weighted player profile](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L616-L659)

### 5. Is PPG projected consistently?

Yes—but it is not counted twice.

Historical scoring is first converted into a rate:

    points per 36 = points per game ÷ minutes per game × 36

The age or career-stage curve changes both scoring rate and playing time. Projected PPG is then rebuilt:

    projected PPG =
        projected points per 36
        × return effectiveness
        × projected minutes
        ÷ 36

For Cooper Flagg:

    23.234 points/36 × 34.535 minutes ÷ 36
    = 22.289 projected PPG

PPG is published for interpretation. It is not added as a second win bonus because PIE already includes scoring and broader box-score impact. Adding both would double-count points.

**Proof in code:** [historical points-per-36 calculation](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/data/fetch_player_stats.py#L300-L313) · [projected PPG](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L743-L803)

### 6. How are injuries included?

There are two layers.

**Historical availability applies to every projected player.** Games played are converted into an 82-game availability rate and combined across recent seasons.

**Current overrides apply only when a sourced recovery situation is entered manually.**

| Player | Low availability | Base | High | Base effectiveness |
|---|---:|---:|---:|---:|
| Kyrie Irving | 61% | 85% | 93% | 94% |
| Jimmy Butler III | 49% | 67% | 85% | 90% |
| Moses Moody | 30% | 51% | 73% | 88% |
| Dereck Lively II | 45% | 70% | 85% | 93% |

The base case produces the published standings. The low and high cases create team-specific ranges that are sampled in the 20,000-season simulation.

The source confirms the injury or recovery status. The numeric ranges are CourtVision assumptions, not medical timetables.

**Proof in code:** [injury application](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L750-L778) · [injury validation](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L935-L979) · [simulation sampling](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/models/simulate.py#L475-L536) · [sourced injury ledger](data/manual/injuries_2026.csv)

CourtVision does **not** currently contain an explicit override for every active NBA injury. The accurate claim is historical availability for all players plus four sourced current-injury scenarios.

---

## THE HONEST ANSWER ON ROSTER FIT

### Does CourtVision know whether a roster has enough shooting, playmaking, rim protection, or a true point guard?

**No—not explicitly.**

The current player layer uses only:

- PIE
- Projected minutes
- Points per 36
- Availability

The source data downloads assists, shooting efficiency, rebounding, usage, and other advanced statistics, but the roster projection does not yet turn them into team-composition features. It also contains no player-position balance, lineup combinations, or pairwise teammate interactions.

What the model captures indirectly:

- Last season’s team strength, which contains some evidence of the previous roster’s fit
- Each player’s realized all-around PIE
- Competition for a fixed 240 minutes
- Availability and return effectiveness

What it does not capture:

- Who initiates the offense
- Whether five good players duplicate the same role
- Spacing and perimeter gravity
- Point-of-attack defense
- Rim protection
- The effect one player has on another player’s shot quality
- Lineup chemistry after a trade

**Proof in code:** [the complete list of player projection targets](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L59-L74) · [player-value formula](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L810-L847)

This is why the Charlotte result deserves skepticism. The model removes LaMelo’s value but does not reduce Kon Knueppel’s efficiency because his primary creator disappeared.

A future fit layer should measure at minimum:

1. Primary creation: assist percentage, usage, and turnover pressure
2. Spacing: three-point volume, efficiency, and off-ball role
3. Interior defense: block rate, defensive rebounding, and opponent rim results
4. Perimeter defense: role-adjusted defensive indicators
5. Positional minutes: whether a roster can fill 48 credible minutes at every role
6. Pair interactions: how returning-player performance changes with major teammates on and off the floor

Until that exists, CourtVision is a roster-value model—not a lineup-chemistry model.

---

## FROM 592 PLAYERS TO 1,230 WINS

The calculation is intentionally constrained.

    effective player value =
        (projected PIE − replacement PIE)
        × allocated minutes / 48
        × 82 games

Availability and return effectiveness modify that value under low, base, and high scenarios.

Every team is normalized to exactly 240 minutes:

    complete 2026–27 roster value
      − actual 2025–26 roster value
      = roster win adjustment

    historical baseline wins
      + roster win adjustment
      = raw projected wins

The 30 raw forecasts are recentered and rounded so the league contains exactly 1,230 wins, 1,230 losses, and 82 games for every team.

**Proof in code:** [minute allocation and player value](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L810-L847) · [full-roster team delta](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_roster_projections.py#L885-L931) · [final standings construction](https://github.com/shreeyahi/court-vision-nba/blob/main/src/courtvision/features/build_offseason_standings.py#L73-L124)

---

## PROOF BEFORE PROJECTION

The development curves were accepted only if they beat a no-change forecast on the held-out 2025–26 player season.

| Target | No-change MAE | Curve MAE | Selected |
|---|---:|---:|---|
| PIE | .01734 | **.01728** | Development curve |
| Minutes per game | 4.603 | **4.434** | Development curve |
| Points per 36 | 2.580 | **2.555** | Development curve |
| Availability | .2227 | **.2199** | Development curve |

The separate team baseline was trained only on prior-season information:

| Split | Seasons |
|---|---|
| Training | Through 2023–24 |
| Validation | 2024–25 |
| Untouched test | 2025–26 |

Its untouched test error was 9.56 MAE wins. That error is carried into the simulations rather than hidden.

[Player backtest](reports/player_projection_backtest.csv) · [Development curves](reports/development_curves_2026_27.csv) · [Model card](docs/model_card.md)

---

## DATA CONTRACT

| Category | Count |
|---|---:|
| Historical regular-season games | 13,209 |
| Historical team seasons | 11 |
| Historical player seasons | 11 |
| Player-season records | 5,968 |
| Unique historical players | 1,554 |
| Projected 2026–27 players | 592 |
| Incoming 2026 drafted rookies | 60 |
| Teams | 30 |
| League wins and losses | 1,230 each |

Transaction states never mix:

- **OFFICIAL** enters the default projection
- **REPORTED** is stored but excluded
- **ON_HOLD** is stored but excluded

Player movement uses NBA IDs whenever available. The 2026 rookie ledger preserves its source and verification date because the NBA statistics Draft History endpoint had not yet published that class when this snapshot was built.

[Trade ledger](data/manual/trades_2026.csv) · [Roster-move ledger](data/manual/roster_moves_2026.csv) · [Data dictionary](docs/data_dictionary.md)

---

## PUBLISHED OUTPUTS

- [Final East and West standings](reports/official_standings_2026_27.csv)
- [All 592 player projections](reports/player_projections_2026_27.csv)
- [Team roster-value changes](reports/team_roster_deltas_2026_27.csv)
- [Age and career-stage curves](reports/development_curves_2026_27.csv)
- [Held-out player backtest](reports/player_projection_backtest.csv)
- [Original transaction-level estimates](reports/trade_player_impacts_2026.csv)

---

## REPRODUCE IT

    git clone https://github.com/shreeyahi/court-vision-nba.git
    cd court-vision-nba

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

    python src/courtvision/data/validate.py
    python src/courtvision/data/fetch_games.py
    python src/courtvision/data/fetch_player_stats.py
    python src/courtvision/data/fetch_projection_inputs.py
    python src/courtvision/features/build_team_seasons.py
    python src/courtvision/models/train_baseline.py
    python src/courtvision/features/build_roster_projections.py
    python src/courtvision/features/build_offseason_standings.py
    python src/courtvision/models/simulate.py

    ruff check src scripts tests
    python -m pytest

Raw NBA downloads, processed caches, and trained model files stay local. Auditable outputs live under reports.

---

## WHAT THIS PROJECT WILL NOT PRETEND

- The 2026 offseason is not finished.
- Current injury overrides are not comprehensive.
- Injury scenarios are assumptions, not medical predictions.
- Draft position is not the same thing as modeling individual NCAA performance.
- Players in the same rookie bucket initially receive the same prior.
- PIE is not a complete defensive or tactical evaluation.
- Roster fit and teammate dependencies are not explicitly modeled.
- A 9.56-win test error means close seeds are uncertain.
- These are forecasts, not guarantees or betting advice.

That uncertainty is part of the result—not an inconvenience to remove from it.

---

## LICENSE

Released under the [MIT License](LICENSE).
