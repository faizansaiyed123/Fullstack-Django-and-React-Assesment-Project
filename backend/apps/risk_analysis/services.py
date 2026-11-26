RISK_LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"]
RISK_RANK = {level: i for i, level in enumerate(RISK_LEVELS)}


def classify_wind(mph):
    if mph is None:
        return None
    if mph >= 55:
        return "No Travel"
    if mph >= 45:
        return "Moderate" if False else "Severe" if mph <= 54 else "No Travel"
    # clean
    if mph >= 45:
        return "Severe"
    if mph >= 35:
        return "High"
    if mph >= 25:
        return "Moderate"
    return "Low"


def classify_wind_clean(mph):
    if mph is None:
        return None
    if mph >= 55:
        return "No Travel"
    if mph >= 45:
        return "Severe"
    if mph >= 35:
        return "High"
    if mph >= 25:
        return "Moderate"
    return "Low"


def classify_rain(in_hr):
    if in_hr is None:
        return None
    if in_hr > 1.00:
        return "No Travel"
    if in_hr > 0.50:
        return "Severe"
    if in_hr > 0.25:
        return "High"
    if in_hr >= 0.10:
        return "Moderate"
    return "Low"


def classify_snow(in_hr):
    if in_hr is None:
        return None
    if in_hr > 3.0:
        return "No Travel"
    if in_hr > 2.0:
        return "Severe"
    if in_hr > 1.0:
        return "High"
    if in_hr >= 0.5:
        return "Moderate"
    return "Low"


def apply_load_rules(wind_risk, wind_mph, load_lb):
    # returns adjusted risk level string
    level = wind_risk
    if wind_mph is None:
        return level
    if wind_mph >= 55:
        return "No Travel"
    if 45 <= wind_mph <= 54 and load_lb > 30000:
        return "No Travel"
    if 35 <= wind_mph <= 44 and load_lb > 40000:
        # Severe
        if RISK_RANK["Severe"] > RISK_RANK.get(level, 0):
            level = "Severe"
    return level


def combine_risks(risks):
    # highest applicable
    best = "Low"
    for r in risks:
        if r is None:
            continue
        if RISK_RANK[r] > RISK_RANK[best]:
            best = r
    return best


def risk_to_score(level):
    return RISK_RANK.get(level, 0)


def classify_checkpoint(weather, load_lb):
    w = weather.get("wind_speed_mph")
    r = weather.get("rain_in_hr")
    s = weather.get("snow_in_hr")
    wr = classify_wind_clean(w)
    rr = classify_rain(r)
    sr = classify_snow(s)
    wr = apply_load_rules(wr, w, load_lb)
    return combine_risks([wr, rr, sr])
