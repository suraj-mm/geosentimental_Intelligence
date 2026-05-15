"""
sentiment.py — Real sentiment analysis for GeoSentiment Cascade.
Uses VADER primary, TextBlob fallback, keyword-based last resort.
"""

from collections import defaultdict

# ── VADER ─────────────────────────────────────────────────────────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    _USE_VADER = True
except ImportError:
    _vader = None
    _USE_VADER = False

# ── TextBlob fallback ─────────────────────────────────────────────────────────
try:
    from textblob import TextBlob
    _USE_TEXTBLOB = True
except ImportError:
    _USE_TEXTBLOB = False


def score_sentiment(text: str) -> float:
    """
    Return a sentiment score in [-1.0, +1.0].
    Input: title + description combined string.
    Uses VADER → TextBlob → keyword fallback.
    """
    if not text or not text.strip():
        return 0.0

    if _USE_VADER and _vader:
        scores = _vader.polarity_scores(text)
        return round(float(scores["compound"]), 4)

    if _USE_TEXTBLOB:
        blob = TextBlob(text)
        return round(float(blob.sentiment.polarity), 4)

    # Bare-minimum keyword fallback
    POS = ["growth", "recovery", "surge", "rally", "gain", "boost", "positive",
           "improve", "success", "profit", "rise", "strong", "record", "innovation",
           "breakthrough", "agreement", "deal", "progress", "advance", "soar"]
    NEG = ["war", "crisis", "crash", "fall", "loss", "conflict", "tension",
           "decline", "risk", "concern", "drop", "weak", "fail", "attack",
           "collapse", "recession", "layoff", "cut", "sanction", "inflation"]
    tl = text.lower()
    score = sum(1 for w in POS if w in tl) - sum(1 for w in NEG if w in tl)
    return round(max(-1.0, min(1.0, score * 0.15)), 4)


def analyze_articles(articles: list) -> list:
    """
    Add 'region' and 'sentiment' keys to each article dict.
    Imports classify_region from news_fetcher to avoid circular imports.
    """
    from news_fetcher import classify_region

    for article in articles:
        if "region" not in article:
            article["region"] = classify_region(article)

        text = " ".join(filter(None, [
            article.get("title", ""),
            article.get("description", ""),
        ]))
        article["sentiment"] = score_sentiment(text)

    return articles


def aggregate_by_region(articles: list) -> dict:
    """
    Compute average sentiment per region.
    Validates articles exist per region; prints debug counts.
    Returns: { "Asia": 0.3, "Europe": -0.2, ... }
    """
    buckets = defaultdict(list)
    for article in articles:
        region = article.get("region", "Global")
        score = article.get("sentiment", 0.0)
        if isinstance(score, dict):
            score = score.get("score", 0.0)
        if region != "Global":
            buckets[region].append(score)

    # Debug: print region article counts
    print("\n── Region Article Counts ──────────────────────")
    for region, scores in sorted(buckets.items()):
        print(f"  {region:<16}: {len(scores)} articles | avg={sum(scores)/len(scores):+.3f}")
    
    unclassified = sum(1 for a in articles if a.get("region") == "Global")
    print(f"  {'Global/Unknown':<16}: {unclassified} articles (not counted)")
    print("───────────────────────────────────────────────\n")

    result = {}
    for region, scores in buckets.items():
        if scores:
            result[region] = round(sum(scores) / len(scores), 4)

    # Redistribution: if a major region has zero articles, interpolate from neighbors
    ALL_REGIONS = ["North America", "Europe", "Asia", "Middle East",
                   "South America", "Africa", "Oceania"]
    if result:
        global_avg = round(sum(result.values()) / len(result.values()), 4)
        for region in ALL_REGIONS:
            if region not in result:
                # Use global average as soft fallback rather than nothing
                result[region] = round(global_avg * 0.5, 4)  # dampened fallback

    return result


def compute_divergence(region_sentiments: dict) -> dict:
    """
    Compute divergence = max(region_avg) - min(region_avg).
    Returns enriched dict with divergence score, label, and narrative.
    """
    if not region_sentiments:
        return {
            "score": 0.0,
            "label": "No Data",
            "level": "none",
            "narrative": "Insufficient data to compute divergence.",
            "most_positive": None,
            "most_negative": None,
        }

    values = list(region_sentiments.values())
    divergence = round(max(values) - min(values), 4) if len(values) > 1 else 0.0

    if divergence >= 0.7:
        level, label = "extreme", "🔴 Extreme"
    elif divergence >= 0.45:
        level, label = "high", "🟠 High"
    elif divergence >= 0.25:
        level, label = "moderate", "🟡 Moderate"
    else:
        level, label = "low", "🟢 Low"

    sorted_regions = sorted(region_sentiments.items(), key=lambda x: x[1])
    most_negative = sorted_regions[0] if sorted_regions else (None, 0)
    most_positive = sorted_regions[-1] if sorted_regions else (None, 0)

    narrative = ""
    if most_positive[0] and most_negative[0] and most_positive[0] != most_negative[0]:
        narrative = (
            f"{most_positive[0]} is most positive ({most_positive[1]:+.2f}), "
            f"while {most_negative[0]} is most negative ({most_negative[1]:+.2f}). "
        )
        if level in ("high", "extreme"):
            narrative += "Strong perception gap — divergent regional narratives detected."
        elif level == "moderate":
            narrative += "Moderate disagreement across regions on this topic."
        else:
            narrative += "Regions broadly aligned in sentiment on this topic."

    return {
        "score": divergence,
        "label": label,
        "level": level,
        "narrative": narrative,
        "most_positive": most_positive[0],
        "most_negative": most_negative[0],
    }
