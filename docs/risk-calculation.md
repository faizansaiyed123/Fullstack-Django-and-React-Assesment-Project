# Risk calculation

All values are converted to the assessment units before classification:
- Wind: mph
- Rain: inches/hour
- Snow: inches/hour

Open-Meteo rain is used for rain classification. Total precipitation is not substituted for rain because it can include snow.

## Wind

| Wind | Risk |
|---|---|
| < 25 mph | Low |
| 25–<35 mph | Moderate |
| 35–<45 mph | High |
| 45–<55 mph | Severe |
| >=55 mph | No Travel |

## Rain

| Rain | Risk |
|---|---|
| < 0.10 in/hr | Low |
| 0.10–<0.25 | Moderate |
| 0.25–<0.50 | High |
| 0.50–1.00 | Severe |
| > 1.00 | No Travel |

## Snow

| Snow | Risk |
|---|---|
| < 0.5 in/hr | Low |
| 0.5–<1.0 | Moderate |
| 1.0–<2.0 | High |
| 2.0–3.0 | Severe |
| > 3.0 | No Travel |

## Load rules

- >=55 mph → No Travel for any load
- 45–<55 mph and load >30,000 lb → No Travel
- 35–<45 mph and load >40,000 lb → Severe

Final checkpoint risk is the highest applicable condition risk when all three required weather values are present. A known No Travel condition takes precedence over missing values in other conditions because it is already a definitive stop condition. Otherwise, if any required wind, rain, or snow value is missing, the overall checkpoint risk is Unable to verify.

## Route metrics

Each checkpoint represents the segment beginning at that checkpoint and ending at the next checkpoint. The final destination checkpoint has zero remaining segment miles.

For each route:
- Severe miles = sum of segments whose checkpoint risk is Severe
- High miles = sum of segments whose checkpoint risk is High
- No Travel miles = sum of segments whose checkpoint risk is No Travel
- Average risk = mileage-weighted risk score across verifiable segment miles

## Recommendation

Among eligible routes, sort lexicographically:
1. Fewest Severe miles
2. Fewest High miles
3. Lowest weighted average risk
4. Shortest travel time

A route with any No Travel checkpoint or any unverified checkpoint is excluded from recommendation and remains visible to the user. This check includes the destination checkpoint even though the destination checkpoint has zero remaining segment miles. No Travel mileage remains a segment-based exposure metric and is not used as the sole safety-eligibility check.
