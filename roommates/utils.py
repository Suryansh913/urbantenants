"""
roommates/utils.py

Simple, dependency-free roommate compatibility scoring.
No AI, no external APIs — pure Python so the weights can be tuned any time.
"""

# Weights must sum to 100. Change these any time to retune the algorithm.
MATCH_WEIGHTS = {
    "budget": 20,
    "location": 20,
    "sharing_type": 15,
    "food_preference": 10,
    "smoking": 10,
    "drinking": 5,
    "sleep_schedule": 10,
    "cleanliness": 5,
    "study_habits": 5,
}


def _budget_score(a, b):
    """
    Overlap-based score between two [min, max] budget ranges.
    Full score if ranges fully overlap, 0 if they don't overlap at all,
    partial score in between.
    """
    if None in (a.budget_min, a.budget_max, b.budget_min, b.budget_max):
        return None

    overlap_low = max(a.budget_min, b.budget_min)
    overlap_high = min(a.budget_max, b.budget_max)

    if overlap_high < overlap_low:
        return 0.0

    overlap = overlap_high - overlap_low
    span_a = max(a.budget_max - a.budget_min, 1)
    span_b = max(b.budget_max - b.budget_min, 1)
    widest_span = max(span_a, span_b, 1)

    return min(overlap / widest_span, 1.0)


def _exact_match_score(val_a, val_b):
    if val_a is None or val_b is None or val_a == "" or val_b == "":
        return None
    return 1.0 if val_a == val_b else 0.0


def calculate_match_percentage(profile_a, profile_b):
    """
    Returns an integer 0-100 compatibility score between two RoommateProfile
    instances. Missing fields are skipped and weights are re-normalised
    across whatever fields *are* comparable, so one missing field never
    unfairly tanks the score.
    """
    field_scorers = {
        "budget": lambda: _budget_score(profile_a, profile_b),
        "location": lambda: _exact_match_score(
            (profile_a.preferred_location or "").strip().lower(),
            (profile_b.preferred_location or "").strip().lower(),
        ),
        "sharing_type": lambda: _exact_match_score(profile_a.sharing_type, profile_b.sharing_type),
        "food_preference": lambda: _exact_match_score(profile_a.food_preference, profile_b.food_preference),
        "smoking": lambda: _exact_match_score(profile_a.smoking, profile_b.smoking),
        "drinking": lambda: _exact_match_score(profile_a.drinking, profile_b.drinking),
        "sleep_schedule": lambda: _exact_match_score(profile_a.sleep_schedule, profile_b.sleep_schedule),
        "cleanliness": lambda: _exact_match_score(profile_a.cleanliness, profile_b.cleanliness),
        "study_habits": lambda: _exact_match_score(profile_a.study_habits, profile_b.study_habits),
    }

    total_weight_used = 0
    weighted_score = 0.0

    for key, scorer in field_scorers.items():
        score = scorer()
        if score is None:
            continue  # skip fields we can't compare
        weight = MATCH_WEIGHTS[key]
        weighted_score += score * weight
        total_weight_used += weight

    if total_weight_used == 0:
        return 0

    percentage = (weighted_score / total_weight_used) * 100
    return int(round(percentage))


def get_recommended_profiles(current_profile, queryset, limit=10):
    """
    Sorts a queryset of RoommateProfile by compatibility with current_profile,
    descending, and returns the top `limit` as a list of (profile, score) tuples.
    Excludes the current user's own profile.
    """
    scored = []
    for profile in queryset.exclude(pk=current_profile.pk):
        score = calculate_match_percentage(current_profile, profile)
        scored.append((profile, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]
