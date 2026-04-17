"""
Auto-generates one-paragraph school diagnosis.
TEMPLATE-BASED — no LLM. Every sentence comes from a conditional branch over
real numbers: gap magnitude, trend direction, last-intervention age.
The output is plain English the DEO can paste into a report or WhatsApp.
"""
from __future__ import annotations


def _gap_label(gap: float) -> str:
    if gap > 25:
        return "critically weak"
    if gap > 12:
        return "significantly below average"
    if gap > 5:
        return "slightly below average"
    return "near the district average"


def _trend_sentence(years_declining: int, subject: str) -> str:
    if years_declining >= 3:
        return (
            f"{subject.title()} has declined in {years_declining} consecutive years — "
            f"this is a structural problem, not a one-year dip."
        )
    if years_declining == 2:
        return f"{subject.title()} has dropped two years running."
    if years_declining == 1:
        return f"{subject.title()} dipped last year. Early action can prevent further decline."
    return f"{subject.title()} is holding steady or improving."


def generate_diagnosis(
    school_name: str,
    reading_pct: float | None,
    math_pct: float | None,
    dist_read_avg: float,
    dist_math_avg: float,
    read_declining: int,
    math_declining: int,
    rank: int,
    total: int,
    months_since: float = 12.0,
) -> str:
    parts = []

    read_gap  = (dist_read_avg - reading_pct)  if reading_pct  is not None else 0.0
    math_gap  = (dist_math_avg - math_pct)     if math_pct     is not None else 0.0

    # Opening sentence with rank
    parts.append(
        f"{school_name} ranks #{rank} of {total} schools in the district "
        f"by urgency score."
    )

    # Reading
    if reading_pct is not None:
        label = _gap_label(read_gap)
        if read_gap > 5:
            parts.append(
                f"Grade 5 reading is {label}: {reading_pct:.0f}% of students can read a story, "
                f"{read_gap:.0f} percentage points below the district average "
                f"({dist_read_avg:.0f}%)."
            )
        else:
            parts.append(
                f"Grade 5 reading is {label} ({reading_pct:.0f}% vs district {dist_read_avg:.0f}%)."
            )
        parts.append(_trend_sentence(read_declining, "reading"))

    # Math
    if math_pct is not None:
        label = _gap_label(math_gap)
        if math_gap > 5:
            parts.append(
                f"Grade 5 math is {label}: {math_pct:.0f}% can solve division problems, "
                f"{math_gap:.0f} pp below district average ({dist_math_avg:.0f}%)."
            )
        else:
            parts.append(
                f"Grade 5 math is {label} ({math_pct:.0f}% vs district {dist_math_avg:.0f}%)."
            )
        parts.append(_trend_sentence(math_declining, "math"))

    # Intervention history
    if months_since >= 18:
        parts.append(f"No intervention has been logged here in the past {int(months_since)} months.")
    elif months_since >= 6:
        parts.append(f"Last intervention was logged {int(months_since)} months ago.")
    else:
        parts.append("An intervention was started recently — check the Tracker for results.")

    # Focus recommendation
    if read_gap >= math_gap:
        focus = "Grade 5 reading and Grade 3 reading"
    else:
        focus = "Grade 5 math and Grade 3 math"
    parts.append(f"**Recommended focus: {focus}.**")

    return " ".join(parts)


def diagnosis_as_plaintext(text: str) -> str:
    """Strip markdown bold for plain-text copy."""
    return text.replace("**", "")
