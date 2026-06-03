"""
stock_engine.py — Real-time stock suggestion engine for GeoSentiment Cascade.
Maps topics → sectors → stocks, fetches live prices via yfinance,
and computes dynamic confidence scores.
"""

import time
import streamlit as st

# ── Topic → Sector mapping ────────────────────────────────────────────────────
TOPIC_SECTOR_MAP = {
    # Preset topics
    "AI & Technology":   ["tech", "semiconductors"],
    "War & Conflict":    ["defense", "energy", "gold"],
    "Economy":           ["banking", "consumer", "reits"],
    "Oil & Energy":      ["energy", "utilities"],
    "Trade & Tariffs":   ["industrials", "shipping", "consumer"],
    "Crypto":            ["crypto", "fintech", "tech"],
    "Climate":           ["renewables", "utilities", "evs"],
    "Politics":          ["defense", "healthcare", "financials"],
    # Dynamic topic keyword → sector
}

# Keyword → sector fallback for custom topics
KEYWORD_SECTOR_MAP = {
    "ai": ["tech", "semiconductors"],
    "artificial intelligence": ["tech", "semiconductors"],
    "machine learning": ["tech", "semiconductors"],
    "nvidia": ["semiconductors", "tech"],
    "chip": ["semiconductors"],
    "semiconductor": ["semiconductors"],
    "war": ["defense", "gold"],
    "conflict": ["defense", "gold"],
    "military": ["defense"],
    "defense": ["defense"],
    "oil": ["energy"],
    "gas": ["energy"],
    "energy": ["energy"],
    "opec": ["energy"],
    "crude": ["energy"],
    "inflation": ["banking", "gold", "commodities"],
    "recession": ["gold", "consumer", "utilities"],
    "economy": ["banking", "consumer", "reits"],
    "gdp": ["banking", "industrials"],
    "interest rate": ["banking", "reits"],
    "fed": ["banking", "reits"],
    "federal reserve": ["banking", "reits"],
    "bitcoin": ["crypto", "fintech"],
    "crypto": ["crypto", "fintech", "tech"],
    "blockchain": ["crypto", "fintech"],
    "ethereum": ["crypto", "fintech"],
    "climate": ["renewables", "utilities", "evs"],
    "green": ["renewables", "evs"],
    "solar": ["renewables", "utilities"],
    "wind": ["renewables", "utilities"],
    "electric vehicle": ["evs", "tech"],
    "ev": ["evs", "tech"],
    "trade": ["industrials", "shipping"],
    "tariff": ["industrials", "consumer"],
    "export": ["industrials", "shipping"],
    "import": ["consumer", "retail"],
    "supply chain": ["industrials", "shipping"],
    "election": ["defense", "healthcare", "financials"],
    "politics": ["defense", "healthcare"],
    "vaccine": ["healthcare", "biotech"],
    "drug": ["healthcare", "biotech"],
    "pharma": ["healthcare", "biotech"],
    "bank": ["banking", "financials"],
    "fintech": ["fintech", "banking"],
    "gold": ["gold", "commodities"],
    "silver": ["commodities"],
    "mining": ["commodities"],
    "real estate": ["reits"],
    "housing": ["reits", "consumer"],
    "tech": ["tech", "semiconductors"],
    "software": ["tech"],
    "cloud": ["tech"],
    "cybersecurity": ["tech", "defense"],
    "space": ["defense", "tech"],
    "retail": ["consumer", "retail"],
    "consumer": ["consumer"],
    "food": ["consumer", "agriculture"],
    "agriculture": ["agriculture"],
    "travel": ["travel", "consumer"],
    "airline": ["travel"],
    "shipping": ["shipping", "industrials"],
    "logistics": ["shipping", "industrials"],
}

# Sector → stock tickers
SECTOR_STOCKS = {
    "tech": [
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"ticker": "META", "name": "Meta Platforms", "sector": "Technology"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Technology"},
    ],
    "semiconductors": [
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "sector": "Semiconductors"},
        {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors"},
        {"ticker": "INTC", "name": "Intel Corp.", "sector": "Semiconductors"},
        {"ticker": "TSM", "name": "Taiwan Semiconductor", "sector": "Semiconductors"},
        {"ticker": "AVGO", "name": "Broadcom Inc.", "sector": "Semiconductors"},
    ],
    "defense": [
        {"ticker": "LMT", "name": "Lockheed Martin", "sector": "Defense"},
        {"ticker": "RTX", "name": "RTX Corporation", "sector": "Defense"},
        {"ticker": "NOC", "name": "Northrop Grumman", "sector": "Defense"},
        {"ticker": "GD", "name": "General Dynamics", "sector": "Defense"},
        {"ticker": "BA", "name": "Boeing Co.", "sector": "Defense/Aerospace"},
    ],
    "energy": [
        {"ticker": "XOM", "name": "ExxonMobil Corp.", "sector": "Energy"},
        {"ticker": "CVX", "name": "Chevron Corp.", "sector": "Energy"},
        {"ticker": "COP", "name": "ConocoPhillips", "sector": "Energy"},
        {"ticker": "SLB", "name": "SLB (Schlumberger)", "sector": "Energy Services"},
        {"ticker": "OXY", "name": "Occidental Petroleum", "sector": "Energy"},
    ],
    "banking": [
        {"ticker": "JPM", "name": "JPMorgan Chase", "sector": "Banking"},
        {"ticker": "BAC", "name": "Bank of America", "sector": "Banking"},
        {"ticker": "GS", "name": "Goldman Sachs", "sector": "Banking"},
        {"ticker": "MS", "name": "Morgan Stanley", "sector": "Banking"},
        {"ticker": "WFC", "name": "Wells Fargo", "sector": "Banking"},
    ],
    "crypto": [
        {"ticker": "COIN", "name": "Coinbase Global", "sector": "Crypto Exchange"},
        {"ticker": "MSTR", "name": "MicroStrategy Inc.", "sector": "Bitcoin Treasury"},
        {"ticker": "RIOT", "name": "Riot Platforms", "sector": "Bitcoin Mining"},
        {"ticker": "MARA", "name": "Marathon Digital", "sector": "Bitcoin Mining"},
        {"ticker": "HOOD", "name": "Robinhood Markets", "sector": "Fintech/Crypto"},
    ],
    "renewables": [
        {"ticker": "NEE", "name": "NextEra Energy", "sector": "Renewables"},
        {"ticker": "ENPH", "name": "Enphase Energy", "sector": "Solar"},
        {"ticker": "SEDG", "name": "SolarEdge Technologies", "sector": "Solar"},
        {"ticker": "FSLR", "name": "First Solar Inc.", "sector": "Solar"},
        {"ticker": "BEP", "name": "Brookfield Renewable", "sector": "Renewables"},
    ],
    "evs": [
        {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Electric Vehicles"},
        {"ticker": "RIVN", "name": "Rivian Automotive", "sector": "Electric Vehicles"},
        {"ticker": "F", "name": "Ford Motor Co.", "sector": "Auto/EVs"},
        {"ticker": "GM", "name": "General Motors", "sector": "Auto/EVs"},
        {"ticker": "NIO", "name": "NIO Inc.", "sector": "Chinese EVs"},
    ],
    "healthcare": [
        {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
        {"ticker": "PFE", "name": "Pfizer Inc.", "sector": "Pharma"},
        {"ticker": "UNH", "name": "UnitedHealth Group", "sector": "Health Insurance"},
        {"ticker": "ABBV", "name": "AbbVie Inc.", "sector": "Biotech/Pharma"},
        {"ticker": "MRK", "name": "Merck & Co.", "sector": "Pharma"},
    ],
    "biotech": [
        {"ticker": "MRNA", "name": "Moderna Inc.", "sector": "Biotech"},
        {"ticker": "BIIB", "name": "Biogen Inc.", "sector": "Biotech"},
        {"ticker": "GILD", "name": "Gilead Sciences", "sector": "Biotech"},
        {"ticker": "REGN", "name": "Regeneron Pharma", "sector": "Biotech"},
    ],
    "gold": [
        {"ticker": "GLD", "name": "SPDR Gold Shares ETF", "sector": "Gold ETF"},
        {"ticker": "NEM", "name": "Newmont Corp.", "sector": "Gold Mining"},
        {"ticker": "GOLD", "name": "Barrick Gold", "sector": "Gold Mining"},
        {"ticker": "IAU", "name": "iShares Gold Trust", "sector": "Gold ETF"},
    ],
    "fintech": [
        {"ticker": "SQ", "name": "Block Inc.", "sector": "Fintech"},
        {"ticker": "PYPL", "name": "PayPal Holdings", "sector": "Fintech"},
        {"ticker": "V", "name": "Visa Inc.", "sector": "Payments"},
        {"ticker": "MA", "name": "Mastercard Inc.", "sector": "Payments"},
    ],
    "consumer": [
        {"ticker": "WMT", "name": "Walmart Inc.", "sector": "Consumer Staples"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer/Retail"},
        {"ticker": "PG", "name": "Procter & Gamble", "sector": "Consumer Staples"},
        {"ticker": "KO", "name": "Coca-Cola Co.", "sector": "Consumer Staples"},
    ],
    "industrials": [
        {"ticker": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials"},
        {"ticker": "HON", "name": "Honeywell International", "sector": "Industrials"},
        {"ticker": "DE", "name": "Deere & Company", "sector": "Agriculture/Machinery"},
        {"ticker": "UPS", "name": "United Parcel Service", "sector": "Logistics"},
    ],
    "shipping": [
        {"ticker": "ZIM", "name": "ZIM Integrated Shipping", "sector": "Shipping"},
        {"ticker": "MATX", "name": "Matson Inc.", "sector": "Shipping"},
        {"ticker": "FDX", "name": "FedEx Corp.", "sector": "Logistics"},
    ],
    "reits": [
        {"ticker": "AMT", "name": "American Tower REIT", "sector": "REIT"},
        {"ticker": "PLD", "name": "Prologis Inc.", "sector": "Industrial REIT"},
        {"ticker": "EQIX", "name": "Equinix Inc.", "sector": "Data Center REIT"},
    ],
    "utilities": [
        {"ticker": "DUK", "name": "Duke Energy Corp.", "sector": "Utilities"},
        {"ticker": "SO", "name": "Southern Company", "sector": "Utilities"},
        {"ticker": "AEP", "name": "American Electric Power", "sector": "Utilities"},
    ],
    "commodities": [
        {"ticker": "FCX", "name": "Freeport-McMoRan", "sector": "Copper/Gold Mining"},
        {"ticker": "VALE", "name": "Vale S.A.", "sector": "Iron Ore Mining"},
        {"ticker": "BHP", "name": "BHP Group", "sector": "Diversified Mining"},
    ],
    "travel": [
        {"ticker": "DAL", "name": "Delta Air Lines", "sector": "Airlines"},
        {"ticker": "MAR", "name": "Marriott International", "sector": "Hotels"},
        {"ticker": "BKNG", "name": "Booking Holdings", "sector": "Travel/OTA"},
    ],
    "financials": [
        {"ticker": "BRK-B", "name": "Berkshire Hathaway B", "sector": "Diversified Finance"},
        {"ticker": "AXP", "name": "American Express", "sector": "Financial Services"},
        {"ticker": "BLK", "name": "BlackRock Inc.", "sector": "Asset Management"},
    ],
    "agriculture": [
        {"ticker": "ADM", "name": "Archer-Daniels-Midland", "sector": "Agriculture"},
        {"ticker": "MOS", "name": "Mosaic Company", "sector": "Fertilizers"},
        {"ticker": "NTR", "name": "Nutrien Ltd.", "sector": "Fertilizers"},
    ],
    "retail": [
        {"ticker": "TGT", "name": "Target Corp.", "sector": "Retail"},
        {"ticker": "COST", "name": "Costco Wholesale", "sector": "Retail"},
        {"ticker": "HD", "name": "Home Depot Inc.", "sector": "Home Improvement"},
    ],
}

# Country-Specific Stock Lists
COUNTRY_STOCKS = {
    "India": [
        {"ticker": "RELIANCE.NS", "name": "Reliance Industries", "country": "India", "exchange": "NSE"},
        {"ticker": "TCS.NS", "name": "Tata Consultancy Services", "country": "India", "exchange": "NSE"},
        {"ticker": "INFY.NS", "name": "Infosys Limited", "country": "India", "exchange": "NSE"},
        {"ticker": "HDFCBANK.NS", "name": "HDFC Bank Limited", "country": "India", "exchange": "NSE"},
        {"ticker": "ICICIBANK.NS", "name": "ICICI Bank Limited", "country": "India", "exchange": "NSE"},
        {"ticker": "LT.NS", "name": "Larsen & Toubro", "country": "India", "exchange": "NSE"},
    ],
    "America": [
        {"ticker": "AAPL", "name": "Apple Inc.", "country": "USA", "exchange": "NASDAQ"},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "country": "USA", "exchange": "NASDAQ"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "country": "USA", "exchange": "NASDAQ"},
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "country": "USA", "exchange": "NASDAQ"},
        {"ticker": "JPM", "name": "JPMorgan Chase", "country": "USA", "exchange": "NYSE"},
        {"ticker": "TSLA", "name": "Tesla Inc.", "country": "USA", "exchange": "NASDAQ"},
    ],
    "England": [
        {"ticker": "HSBA.L", "name": "HSBC Holdings", "country": "UK", "exchange": "LSE"},
        {"ticker": "LLOY.L", "name": "Lloyds Banking Group", "country": "UK", "exchange": "LSE"},
        {"ticker": "BP.L", "name": "BP plc", "country": "UK", "exchange": "LSE"},
        {"ticker": "SHELL.L", "name": "Shell plc", "country": "UK", "exchange": "LSE"},
        {"ticker": "GLEN.L", "name": "Glencore plc", "country": "UK", "exchange": "LSE"},
        {"ticker": "DGE.L", "name": "Diageo plc", "country": "UK", "exchange": "LSE"},
    ],
    "Japan": [
        {"ticker": "9984.T", "name": "SoftBank Group Corp.", "country": "Japan", "exchange": "TSE"},
        {"ticker": "6758.T", "name": "Sony Group Corporation", "country": "Japan", "exchange": "TSE"},
        {"ticker": "7203.T", "name": "Toyota Motor Corp.", "country": "Japan", "exchange": "TSE"},
        {"ticker": "8035.T", "name": "Tokyo Electron Limited", "country": "Japan", "exchange": "TSE"},
        {"ticker": "9432.T", "name": "Nippon Telegraph & Telephone", "country": "Japan", "exchange": "TSE"},
        {"ticker": "8306.T", "name": "Mitsubishi UFJ Financial", "country": "Japan", "exchange": "TSE"},
    ],
    "China": [
        {"ticker": "BABA", "name": "Alibaba Group Holding", "country": "China", "exchange": "NYSE"},
        {"ticker": "PDD", "name": "PinDuoDuo Inc.", "country": "China", "exchange": "NASDAQ"},
        {"ticker": "NTES", "name": "NetEase Inc.", "country": "China", "exchange": "NASDAQ"},
        {"ticker": "JD", "name": "JD.com Inc.", "country": "China", "exchange": "NASDAQ"},
        {"ticker": "TCEHY", "name": "Tencent Holdings", "country": "China", "exchange": "OTC"},
        {"ticker": "NIO", "name": "NIO Inc.", "country": "China", "exchange": "NYSE"},
    ],
    "Iran": [
        {"ticker": "SAPCO.IR", "name": "Saipa Co. Ltd.", "country": "Iran", "exchange": "Tehran"},
        {"ticker": "KCHOL.IR", "name": "Khodro Company", "country": "Iran", "exchange": "Tehran"},
        {"ticker": "IMMC.IR", "name": "Iran Minerals Company", "country": "Iran", "exchange": "Tehran"},
        {"ticker": "NIOPDC.IR", "name": "National Iranian Oil Products", "country": "Iran", "exchange": "Tehran"},
    ],
}


def get_sectors_for_topic(topic: str) -> list:
    """
    Map a topic string to relevant sectors.
    Checks preset map first, then keyword scan.
    """
    # Direct preset match
    if topic in TOPIC_SECTOR_MAP:
        return TOPIC_SECTOR_MAP[topic]

    # Keyword scan on custom topic
    topic_lower = topic.lower()
    matched_sectors = []
    for keyword, sectors in KEYWORD_SECTOR_MAP.items():
        if keyword in topic_lower:
            for s in sectors:
                if s not in matched_sectors:
                    matched_sectors.append(s)

    return matched_sectors if matched_sectors else ["tech", "banking"]


def get_stock_candidates(topic: str, max_stocks: int = 6) -> list:
    """
    Get candidate stock tickers for a topic.
    Returns list of stock dicts with ticker, name, sector.
    """
    sectors = get_sectors_for_topic(topic)
    candidates = []
    seen_tickers = set()

    for sector in sectors:
        stocks = SECTOR_STOCKS.get(sector, [])
        for stock in stocks:
            if stock["ticker"] not in seen_tickers:
                candidates.append(stock.copy())
                seen_tickers.add(stock["ticker"])
            if len(candidates) >= max_stocks:
                break
        if len(candidates) >= max_stocks:
            break

    return candidates[:max_stocks]


def get_country_stocks(country: str, max_stocks: int = 6) -> list:
    """
    Get country-specific stock candidates.
    Returns list of stock dicts for the given country.
    """
    stocks = COUNTRY_STOCKS.get(country, [])
    return stocks[:max_stocks]


@st.cache_data(ttl=120)  # 2-min cache for stock prices
def fetch_stock_data(ticker: str) -> dict:
    """
    Fetch real-time stock data using yfinance.
    Returns dict with price, change_pct, prev_close, volume.
    Falls back to None values on error.
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.fast_info

        current_price = getattr(info, "last_price", None)
        prev_close = getattr(info, "previous_close", None)

        if current_price and prev_close and prev_close > 0:
            change_pct = ((current_price - prev_close) / prev_close) * 100
        else:
            change_pct = 0.0

        # 5-day history for trend calculation
        hist = stock.history(period="5d")
        price_trend = 0.0
        if not hist.empty and len(hist) >= 2:
            week_ago = hist["Close"].iloc[0]
            today = hist["Close"].iloc[-1]
            price_trend = (today - week_ago) / week_ago if week_ago > 0 else 0.0

        return {
            "price": round(float(current_price), 2) if current_price else None,
            "prev_close": round(float(prev_close), 2) if prev_close else None,
            "change_pct": round(float(change_pct), 2),
            "price_trend": round(float(price_trend), 4),
            "volume": getattr(info, "three_month_average_volume", None),
            "error": None,
        }

    except Exception as e:
        return {
            "price": None,
            "prev_close": None,
            "change_pct": 0.0,
            "price_trend": 0.0,
            "volume": None,
            "error": str(e),
        }


def compute_confidence(
    sentiment_score: float,
    news_count: int,
    price_trend: float,
) -> float:
    """
    Compute dynamic confidence score (0–100).

    Formula:
      sentiment_strength * 0.50  — how strong/clear the sentiment signal is
      news_volume_factor  * 0.30  — how much news coverage exists
      price_trend_factor  * 0.20  — stock trend alignment with sentiment

    All factors normalized to [0, 1] before weighting.
    """
    # Sentiment strength: how far from zero (strong signal either way)
    sentiment_strength = min(abs(sentiment_score) / 1.0, 1.0)

    # News volume factor: log-normalized, 50 articles = ~1.0
    import math
    news_volume_factor = min(math.log1p(news_count) / math.log1p(50), 1.0)

    # Price trend factor: normalize [-0.1, +0.1] range to [0, 1]
    # Alignment: positive sentiment + upward trend = high confidence
    trend_alignment = sentiment_score * price_trend  # same sign = positive
    price_trend_factor = min(max((trend_alignment + 0.01) / 0.02, 0.0), 1.0)

    raw = (
        sentiment_strength  * 0.50 +
        news_volume_factor  * 0.30 +
        price_trend_factor  * 0.20
    )

    # Scale to 40–95% range (avoid 0% or 100% extremes)
    confidence = 40 + (raw * 55)
    return round(confidence, 1)


def get_stock_suggestions(
    topic: str,
    sentiment_score: float,
    news_count: int,
    max_stocks: int = 6,
) -> list:
    """
    Main entry: return list of stock suggestion dicts with live data.

    Each dict:
      ticker, name, sector, price, change_pct, confidence, error
    """
    candidates = get_stock_candidates(topic, max_stocks=max_stocks)
    results = []

    for stock in candidates:
        ticker = stock["ticker"]
        market_data = fetch_stock_data(ticker)

        price_trend = market_data.get("price_trend", 0.0)
        confidence = compute_confidence(sentiment_score, news_count, price_trend)

        results.append({
            "ticker": ticker,
            "name": stock["name"],
            "sector": stock["sector"],
            "price": market_data["price"],
            "change_pct": market_data["change_pct"],
            "price_trend_5d": price_trend,
            "confidence": confidence,
            "error": market_data["error"],
        })

    return results


def get_country_stock_suggestions(
    country: str,
    sentiment_score: float,
    news_count: int,
    max_stocks: int = 6,
) -> list:
    """
    Get country-specific stock suggestions with live data.
    
    Each dict:
      ticker, name, country, exchange, price, change_pct, confidence, error
    """
    candidates = get_country_stocks(country, max_stocks=max_stocks)
    results = []

    for stock in candidates:
        ticker = stock["ticker"]
        market_data = fetch_stock_data(ticker)

        price_trend = market_data.get("price_trend", 0.0)
        confidence = compute_confidence(sentiment_score, news_count, price_trend)

        results.append({
            "ticker": ticker,
            "name": stock["name"],
            "country": stock.get("country", country),
            "exchange": stock.get("exchange", ""),
            "price": market_data["price"],
            "change_pct": market_data["change_pct"],
            "price_trend_5d": price_trend,
            "confidence": confidence,
            "error": market_data["error"],
        })

    return results
