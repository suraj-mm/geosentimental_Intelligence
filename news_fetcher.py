"""
news_fetcher.py — Topic-based news fetching for GeoSentiment Cascade.
Cache is keyed by topic — changing topic busts the cache automatically.
"""

import re
import requests
import streamlit as st
from collections import defaultdict

NEWS_API_KEY = "aeb5b697d5a94ff1a6c7c3cb9ae0dc10"
NEWS_API_URL = "https://newsapi.org/v2/everything"

TOPIC_QUERIES = {
    "AI & Technology":   "artificial intelligence technology OR AI OR machine learning",
    "War & Conflict":    "war conflict military OR warfare OR ceasefire OR troops",
    "Economy":           "economy economic GDP inflation OR recession OR growth",
    "Oil & Energy":      "oil OPEC energy crude OR fuel OR gas OR petroleum",
    "Trade & Tariffs":   "trade tariffs export import OR sanctions OR WTO",
    "Crypto":            "cryptocurrency bitcoin ethereum OR blockchain OR crypto",
    "Climate":           "climate change environment emissions OR global warming",
    "Politics":          "politics election government OR president OR parliament",
}

SOURCE_REGION_MAP = {
    "reuters.com": "North America", "bloomberg.com": "North America",
    "nytimes.com": "North America", "wsj.com": "North America",
    "washingtonpost.com": "North America", "cnn.com": "North America",
    "foxnews.com": "North America", "apnews.com": "North America",
    "cbsnews.com": "North America", "nbcnews.com": "North America",
    "politico.com": "North America", "thehill.com": "North America",
    "globeandmail.com": "North America", "cbc.ca": "North America",
    "axios.com": "North America", "usatoday.com": "North America",
    "cnbc.com": "North America", "techcrunch.com": "North America",
    "wired.com": "North America", "theverge.com": "North America",
    "arstechnica.com": "North America", "forbes.com": "North America",
    "businessinsider.com": "North America", "marketwatch.com": "North America",
    "coindesk.com": "North America", "cointelegraph.com": "North America",
    "bbc.com": "Europe", "bbc.co.uk": "Europe",
    "theguardian.com": "Europe", "ft.com": "Europe",
    "economist.com": "Europe", "euronews.com": "Europe",
    "dw.com": "Europe", "spiegel.de": "Europe",
    "lemonde.fr": "Europe", "corriere.it": "Europe",
    "elpais.com": "Europe", "independent.co.uk": "Europe",
    "telegraph.co.uk": "Europe", "sky.com": "Europe",
    "politico.eu": "Europe", "rferl.org": "Europe",
    "euractiv.com": "Europe", "irishtimes.com": "Europe",
    "scmp.com": "Asia", "timesofindia.com": "Asia",
    "hindustantimes.com": "Asia", "ndtv.com": "Asia",
    "japantimes.co.jp": "Asia", "asahi.com": "Asia",
    "koreatimes.co.kr": "Asia", "straitstimes.com": "Asia",
    "channelnewsasia.com": "Asia", "globaltimes.cn": "Asia",
    "xinhuanet.com": "Asia", "bangkokpost.com": "Asia",
    "nikkei.com": "Asia", "thehindu.com": "Asia",
    "economictimes.com": "Asia", "livemint.com": "Asia",
    "wionews.com": "Asia", "firstpost.com": "Asia",
    "aljazeera.com": "Middle East", "arabnews.com": "Middle East",
    "thenationalnews.com": "Middle East", "gulfnews.com": "Middle East",
    "haaretz.com": "Middle East", "timesofisrael.com": "Middle East",
    "iran-daily.com": "Middle East", "dailysabah.com": "Middle East",
    "middleeasteye.net": "Middle East", "alarabiya.net": "Middle East",
    "jpost.com": "Middle East",
    "mercopress.com": "South America", "buenosairesherald.com": "South America",
    "folha.uol.com.br": "South America",
    "dailymaverick.co.za": "Africa", "nation.africa": "Africa",
    "theeastafrican.co.ke": "Africa", "guardian.ng": "Africa",
    "abc.net.au": "Oceania", "smh.com.au": "Oceania",
    "nzherald.co.nz": "Oceania", "rnz.co.nz": "Oceania",
}

SOURCE_NAME_MAP = {
    "cnn": "North America", "bbc": "Europe", "bbc news": "Europe",
    "the guardian": "Europe", "reuters": "North America",
    "bloomberg": "North America", "the new york times": "North America",
    "the wall street journal": "North America", "associated press": "North America",
    "fox news": "North America", "nbc news": "North America",
    "cbs news": "North America", "cnbc": "North America",
    "politico": "North America", "axios": "North America",
    "techcrunch": "North America", "the verge": "North America",
    "wired": "North America", "financial times": "Europe",
    "the economist": "Europe", "euronews": "Europe",
    "deutsche welle": "Europe", "dw": "Europe",
    "sky news": "Europe", "the independent": "Europe",
    "the telegraph": "Europe", "le monde": "Europe",
    "south china morning post": "Asia", "the times of india": "Asia",
    "hindustan times": "Asia", "ndtv": "Asia",
    "the japan times": "Asia", "nikkei": "Asia",
    "the straits times": "Asia", "channel news asia": "Asia",
    "channel newsasia": "Asia", "global times": "Asia",
    "xinhua": "Asia", "al jazeera": "Middle East",
    "aljazeera": "Middle East", "arab news": "Middle East",
    "the national": "Middle East", "gulf news": "Middle East",
    "haaretz": "Middle East", "the times of israel": "Middle East",
    "middle east eye": "Middle East", "daily sabah": "Middle East",
    "abc australia": "Oceania", "sydney morning herald": "Oceania",
    "new zealand herald": "Oceania", "coindesk": "North America",
    "cointelegraph": "North America",
}

REGION_KEYWORDS = {
    "Asia": [
        "china", "chinese", "beijing", "shanghai", "japan", "japanese", "tokyo",
        "korea", "korean", "india", "indian", "mumbai", "delhi", "bangalore",
        "asia", "asian", "singapore", "hong kong", "taiwan", "vietnam",
        "indonesia", "thailand", "malaysia", "pakistan", "bangladesh",
        "modi", "xi jinping", "seoul", "kathmandu",
    ],
    "Europe": [
        "europe", "european", "eu", "germany", "german", "berlin", "france",
        "french", "paris", "uk", "britain", "british", "london", "italy",
        "italian", "rome", "spain", "spanish", "madrid", "netherlands",
        "dutch", "sweden", "norway", "denmark", "poland", "ukraine",
        "russia", "moscow", "nato", "brussels", "macron", "scholz",
        "ecb", "eurozone",
    ],
    "North America": [
        "us", "usa", "united states", "america", "american", "washington",
        "new york", "california", "canada", "canadian", "toronto", "mexico",
        "federal reserve", "fed", "wall street", "nasdaq", "dow jones",
        "white house", "congress", "senate", "trump", "biden",
        "silicon valley",
    ],
    "Middle East": [
        "middle east", "saudi", "arabia", "riyadh", "israel", "israeli",
        "tel aviv", "iran", "iranian", "tehran", "iraq", "baghdad",
        "turkey", "turkish", "ankara", "uae", "dubai", "abu dhabi",
        "qatar", "kuwait", "opec", "persian gulf", "gaza", "lebanon",
        "syria", "yemen", "hamas", "hezbollah", "erdogan", "netanyahu",
    ],
    "South America": [
        "brazil", "argentina", "colombia", "chile", "peru", "venezuela",
        "south america", "latin america", "buenos aires", "bogota",
        "santiago", "rio", "sao paulo", "brasilia", "lula", "milei",
    ],
    "Africa": [
        "africa", "african", "nigeria", "kenya", "south africa", "ethiopia",
        "egypt", "ghana", "tanzania", "uganda", "rwanda", "zimbabwe",
        "lagos", "nairobi", "cairo", "johannesburg", "cape town",
    ],
    "Oceania": [
        "australia", "australian", "sydney", "melbourne", "new zealand",
        "auckland", "canberra", "brisbane", "perth",
        "reserve bank of australia",
    ],
}


def classify_region(article: dict) -> str:
    """
    Classify article into region using:
    1. Source URL domain lookup
    2. Source display name lookup
    3. Keyword scan in title + description + content
    4. Fallback: Global
    """
    source = article.get("source", {})
    source_name = (source.get("name", "") if isinstance(source, dict) else str(source)).lower().strip()
    url = article.get("url", "").lower()

    # 1. Domain from URL
    for domain, region in SOURCE_REGION_MAP.items():
        if domain in url:
            return region

    # 2. Source display name
    for name_key, region in SOURCE_NAME_MAP.items():
        if name_key in source_name:
            return region

    # 3. Keyword scan
    text = " ".join(filter(None, [
        article.get("title", ""),
        article.get("description", ""),
        article.get("content", ""),
    ])).lower()

    region_hits = defaultdict(int)
    for region, keywords in REGION_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                region_hits[region] += 1

    if region_hits:
        return max(region_hits, key=region_hits.get)

    return "Global"


@st.cache_data(ttl=300)
def fetch_news_by_topic(topic: str, page_size: int = 50) -> list:
    """
    Fetch news articles for a given topic string.
    Cache key = topic, so changing topic automatically busts cache.
    """
    query = TOPIC_QUERIES.get(topic, topic)
    params = {
        "q":        query,
        "sortBy":   "publishedAt",
        "pageSize": min(page_size, 100),
        "language": "en",
        "apiKey":   NEWS_API_KEY,
    }
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        data = response.json()
        if response.status_code == 200:
            articles = data.get("articles", [])
            articles = [
                a for a in articles
                if a.get("title") and a["title"] != "[Removed]"
                and a.get("source", {}).get("name", "") != "[Removed]"
            ]
            return articles
        else:
            st.error(f"❌ News API Error ({response.status_code}): {data.get('message', 'Unknown error')}")
            return []
    except requests.exceptions.Timeout:
        st.error("❌ News API timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not reach News API. Check your internet connection.")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error fetching news: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_news_by_region(region: str, topic: str = "") -> list:
    """Fetch region-specific news — used when a globe point is clicked."""
    REGION_QUERIES = {
        "Global":        "world news",
        "Asia":          "Asia China Japan India news",
        "Europe":        "Europe EU Britain Germany France news",
        "North America": "United States Canada news",
        "South America": "South America Brazil Argentina Latin America news",
        "Africa":        "Africa Nigeria Kenya South Africa news",
        "Middle East":   "Middle East Saudi Israel Iran news geopolitics",
        "Oceania":       "Australia New Zealand Oceania news",
    }
    base_query = REGION_QUERIES.get(region, region + " news")
    query = f"({base_query}) AND ({topic})" if topic else base_query
    params = {
        "q":        query,
        "sortBy":   "publishedAt",
        "pageSize": 8,
        "language": "en",
        "apiKey":   NEWS_API_KEY,
    }
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        data = response.json()
        if response.status_code == 200:
            articles = data.get("articles", [])
            return [a for a in articles if a.get("title") and a["title"] != "[Removed]"][:8]
        return []
    except Exception:
        return []
