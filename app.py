"""
app.py — GeoSentiment Cascade
Real-time geopolitical sentiment analysis with live stock suggestions.
"""

import streamlit as st
from globe_component import render_globe
from news_fetcher import fetch_news_by_topic, fetch_news_by_region, TOPIC_QUERIES
from sentiment import analyze_articles, aggregate_by_region, compute_divergence
from stock_engine import get_stock_suggestions, get_country_stock_suggestions

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GeoSentiment Cascade",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  .stApp {
    background: linear-gradient(135deg, #05051a 0%, #080820 50%, #0a0a1e 100%);
    color: #e0e0f0;
  }

  h1 {
    background: linear-gradient(90deg, #00ffc8, #7b61ff, #00c8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2rem !important;
    padding-bottom: 4px;
  }

  h2, h3 {
    color: #c0c0e0 !important;
    font-weight: 600;
  }

  /* ── Topic selector ── */
  .topic-bar {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,255,200,0.15);
    border-radius: 14px;
    padding: 14px 20px;
    margin-bottom: 16px;
  }

  /* ── Divergence banner ── */
  .divergence-banner {
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 14px;
    text-align: center;
  }
  .divergence-extreme { background: linear-gradient(135deg, #3a0a0a, #1a0505); border: 1px solid #ff525255; }
  .divergence-high    { background: linear-gradient(135deg, #2a1500, #180c00); border: 1px solid #ff922b55; }
  .divergence-moderate{ background: linear-gradient(135deg, #1e1a00, #100e00); border: 1px solid #ffeb3b55; }
  .divergence-low     { background: linear-gradient(135deg, #001a0e, #000e07); border: 1px solid #00e67655; }
  .divergence-none    { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); }

  .divergence-score {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
  }
  .divergence-label {
    font-size: 0.95rem;
    font-weight: 600;
    margin-top: 2px;
    opacity: 0.9;
  }
  .divergence-narrative {
    font-size: 0.78rem;
    color: #8080a0;
    margin-top: 8px;
    line-height: 1.5;
  }

  /* ── Region sentiment bars ── */
  .region-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 7px 0;
    font-size: 13px;
  }
  .region-name {
    min-width: 110px;
    color: #c0c0e0;
    font-weight: 500;
  }
  .sentiment-bar-bg {
    flex: 1;
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    overflow: hidden;
  }
  .sentiment-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
  }
  .sentiment-value {
    min-width: 46px;
    text-align: right;
    font-size: 12px;
    font-weight: 600;
  }

  /* ── News card ── */
  .news-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s ease;
  }
  .news-card:hover {
    border-color: rgba(0,255,200,0.3);
  }

  /* ── Region / sentiment badges ── */
  .badge-row {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .badge-region {
    background: linear-gradient(90deg, #00ffc822, #7b61ff22);
    border: 1px solid rgba(0,255,200,0.35);
    color: #00ffc8;
  }
  .badge-positive { background: rgba(0,230,118,0.12); border: 1px solid #00e67644; color: #00e676; }
  .badge-neutral  { background: rgba(255,235,59,0.10); border: 1px solid #ffeb3b44; color: #ffeb3b; }
  .badge-negative { background: rgba(255,82,82,0.12);  border: 1px solid #ff525244; color: #ff5252; }

  .news-meta { font-size: 11px; color: #7070a0; margin-top: 4px; }

  /* ── Stock card ── */
  .stock-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(123,97,255,0.2);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
  }
  .stock-ticker {
    font-size: 15px;
    font-weight: 700;
    color: #7b61ff;
    letter-spacing: 0.05em;
  }
  .stock-name {
    font-size: 11px;
    color: #7070a0;
    margin-top: 1px;
  }
  .stock-price {
    font-size: 16px;
    font-weight: 700;
    color: #e0e0f0;
  }
  .stock-change-pos { color: #00e676; font-size: 12px; font-weight: 600; }
  .stock-change-neg { color: #ff5252; font-size: 12px; font-weight: 600; }
  .stock-change-neu { color: #ffeb3b; font-size: 12px; font-weight: 600; }
  .confidence-bar-bg {
    height: 5px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    margin-top: 8px;
    overflow: hidden;
  }
  .confidence-bar-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #7b61ff, #00ffc8);
  }

  hr { border-color: rgba(255,255,255,0.06) !important; }
  .element-container iframe { border-radius: 12px; }
  #MainMenu, footer, header { visibility: hidden; }

  .stSelectbox > div > div { background: rgba(255,255,255,0.05) !important; border-color: rgba(0,255,200,0.2) !important; }
  .stTextInput > div > div { background: rgba(255,255,255,0.05) !important; }
</style>
""", unsafe_allow_html=True)


# ── Session State Bootstrap ────────────────────────────────────────────────────
if "selected_region" not in st.session_state:
    st.session_state.selected_region = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "AI & Technology"
if "region_sentiments" not in st.session_state:
    st.session_state.region_sentiments = {}
if "divergence" not in st.session_state:
    st.session_state.divergence = {}


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 🌍 GeoSentiment Cascade")
st.markdown(
    "<p style='color:#7070a0; margin-top:-10px; margin-bottom:16px; font-size:14px;'>"
    "Compare how different regions of the world feel about the same topic — in real time."
    "</p>",
    unsafe_allow_html=True,
)

# ── Topic Selector (TASK 1: Search bar connected) ──────────────────────────────
st.markdown("<div class='topic-bar'>", unsafe_allow_html=True)
topic_col1, topic_col2 = st.columns([3, 1])

with topic_col1:
    preset_topics = list(TOPIC_QUERIES.keys())
    selected_preset = st.selectbox(
        "🔍 Select a Topic",
        options=["Custom…"] + preset_topics,
        index=preset_topics.index(st.session_state.current_topic) + 1
            if st.session_state.current_topic in preset_topics else 0,
        label_visibility="visible",
    )

with topic_col2:
    custom_topic = ""
    if selected_preset == "Custom…":
        custom_topic = st.text_input(
            "Custom topic",
            placeholder="e.g. semiconductors",
            label_visibility="collapsed",
            key="custom_topic_input",
        )

st.markdown("</div>", unsafe_allow_html=True)

# Resolve active topic
active_topic = (
    custom_topic.strip()
    if selected_preset == "Custom…" and custom_topic.strip()
    else (selected_preset if selected_preset != "Custom…" else "")
)

if not active_topic:
    active_topic = st.session_state.current_topic

# TASK 1: Detect topic change → clear cache + state
if active_topic != st.session_state.current_topic:
    st.session_state.current_topic = active_topic
    st.session_state.selected_region = None
    st.session_state.region_sentiments = {}
    st.session_state.divergence = {}
    # Clear Streamlit's cache so fresh API call fires
    fetch_news_by_topic.clear()

st.divider()


# ── Fetch & Analyze ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_intelligence(topic: str):
    """Fetch news, run sentiment, aggregate by region, compute divergence."""
    articles = fetch_news_by_topic(topic, page_size=50)
    if not articles:
        return [], {}, {}

    analyzed = analyze_articles(articles)

    # TASK 2: Validate articles exist before processing
    if not analyzed:
        return [], {}, {}

    region_sentiments = aggregate_by_region(analyzed)
    divergence = compute_divergence(region_sentiments)
    return analyzed, region_sentiments, divergence


with st.spinner(f"Analyzing global sentiment on **{active_topic}**…"):
    all_articles, region_sentiments, divergence = get_intelligence(active_topic)

# Update session state
st.session_state.region_sentiments = region_sentiments
st.session_state.divergence = divergence

# ── Layout: Globe (left) | Intel + News (right) ────────────────────────────────
col_globe, col_right = st.columns([3, 2], gap="large")

with col_globe:
    st.markdown("### 🌐 Interactive Globe")
    st.markdown(
        "<p style='color:#6060a0; font-size:12px; margin-top:-8px;'>"
        "Globe points colored by regional sentiment · click to filter news</p>",
        unsafe_allow_html=True,
    )

    clicked_region = render_globe(
        region_sentiments=region_sentiments,
        key="globe",
    )

    if clicked_region and clicked_region != st.session_state.selected_region:
        st.session_state.selected_region = clicked_region
        st.rerun()

    # ── TASK 5–6: Stock Suggestions Panel (below globe) ────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Live Stock Intelligence")
    st.markdown(
        "<p style='color:#6060a0; font-size:12px; margin-top:-8px;'>"
        f"Sector picks driven by <strong style='color:#7b61ff'>{active_topic}</strong> sentiment · refreshes every 2 min</p>",
        unsafe_allow_html=True,
    )

    # Compute overall average sentiment for confidence formula
    avg_sentiment = (
        sum(region_sentiments.values()) / len(region_sentiments)
        if region_sentiments else 0.0
    )
    news_count = len(all_articles)

    with st.spinner("Fetching live stock data…"):
        stocks = get_stock_suggestions(
            topic=active_topic,
            sentiment_score=avg_sentiment,
            news_count=news_count,
            max_stocks=6,
        )

    if stocks:
        # Display each stock card
        for stock in stocks:
            price = stock.get("price")
            change = stock.get("change_pct", 0.0)
            confidence = stock.get("confidence", 50.0)
            error = stock.get("error")

            price_str = f"${price:,.2f}" if price else "—"
            if change > 0:
                change_str = f"▲ {change:+.2f}%"
                change_class = "stock-change-pos"
            elif change < 0:
                change_str = f"▼ {change:.2f}%"
                change_class = "stock-change-neg"
            else:
                change_str = f"◆ {change:.2f}%"
                change_class = "stock-change-neu"

            conf_color = (
                "#00e676" if confidence >= 70 else
                "#ffeb3b" if confidence >= 50 else
                "#ff5252"
            )

            st.markdown(f"""
            <div class="stock-card">
              <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                  <div class="stock-ticker">{stock['ticker']}</div>
                  <div class="stock-name">{stock['name']}</div>
                  <div style="font-size:10px; color:#5050a0; margin-top:2px;">{stock['sector']}</div>
                </div>
                <div style="text-align:right;">
                  <div class="stock-price">{price_str}</div>
                  <div class="{change_class}">{change_str}</div>
                </div>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                <span style="font-size:10px; color:#6060a0;">Confidence</span>
                <span style="font-size:11px; font-weight:700; color:{conf_color};">{confidence:.0f}%</span>
              </div>
              <div class="confidence-bar-bg">
                <div class="confidence-bar-fill" style="width:{confidence}%;"></div>
              </div>
              {"<div style='font-size:9px; color:#504060; margin-top:4px;'>⚠ Price unavailable (market closed or API limit)</div>" if error else ""}
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            "<p style='color:#3a3a5a; font-size:10px; margin-top:4px;'>"
            "⚠ Not financial advice. Confidence = sentiment × news volume × price trend.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No stock suggestions available for this topic.")


with col_right:

    # ── Divergence Banner ──────────────────────────────────────────────────────
    if divergence:
        div_score   = divergence.get("score", 0.0)
        div_label   = divergence.get("label", "—")
        div_level   = divergence.get("level", "none")
        div_narrative = divergence.get("narrative", "")

        st.markdown(f"""
        <div class="divergence-banner divergence-{div_level}">
          <div style="font-size:11px; color:#6060a0; text-transform:uppercase;
                      letter-spacing:0.08em; margin-bottom:4px;">
            🔀 Narrative Divergence Score
          </div>
          <div class="divergence-score">{div_score:.2f}</div>
          <div class="divergence-label">{div_label}</div>
          {f'<div class="divergence-narrative">{div_narrative}</div>' if div_narrative else ''}
        </div>
        """, unsafe_allow_html=True)

    elif not all_articles:
        st.warning("⚠ No articles found for this topic. Try a different search term.")

    # ── Region Sentiment Summary ───────────────────────────────────────────────
    if region_sentiments:
        st.markdown(
            "<p style='font-size:12px; color:#6060a0; text-transform:uppercase;"
            " letter-spacing:0.07em; margin-bottom:6px;'>📊 Regional Sentiment</p>",
            unsafe_allow_html=True,
        )

        # Separate regions and countries
        ORDERED_REGIONS = ["North America", "Europe", "Asia", "Middle East",
                           "South America", "Africa", "Oceania"]
        ORDERED_COUNTRIES = ["India", "America", "England", "Japan", "China", "Iran"]

        # Display Regions first
        for region in ORDERED_REGIONS:
            score = region_sentiments.get(region)
            if score is None:
                continue

            pct = int((score + 1) / 2 * 100)
            bar_color = "#00e676" if score >= 0.15 else "#ff5252" if score <= -0.15 else "#ffeb3b"

            if score >= 0:
                bar_left  = "50%"
                bar_width = f"{pct - 50}%"
            else:
                bar_left  = f"{pct}%"
                bar_width = f"{50 - pct}%"

            st.markdown(f"""
            <div class="region-row">
              <span class="region-name" style="color:#c0c0e0;">{region}</span>
              <div class="sentiment-bar-bg">
                <div class="sentiment-bar-fill"
                     style="background:{bar_color}; width:{bar_width}; margin-left:{bar_left};"></div>
              </div>
              <span class="sentiment-value" style="color:{bar_color}">
                {'+' if score >= 0 else ''}{score:.2f}
              </span>
            </div>
            """, unsafe_allow_html=True)

        # Display Countries
        st.markdown(
            "<p style='font-size:11px; color:#7070a0; text-transform:uppercase;"
            " letter-spacing:0.07em; margin-top:10px; margin-bottom:6px;'>🌍 Country Sentiment (Tap to View)</p>",
            unsafe_allow_html=True,
        )

        for country in ORDERED_COUNTRIES:
            score = region_sentiments.get(country)
            
            col_display, col_btn = st.columns([0.9, 0.1])
            
            with col_display:
                if score is None:
                    # Show country even without data
                    st.markdown(f"""
                    <div class="region-row">
                      <span class="region-name" style="color:#00ffc8; font-weight:600;">{country}</span>
                      <div class="sentiment-bar-bg">
                        <div class="sentiment-bar-fill" style="background:#4a4a6a; width:50%;"></div>
                      </div>
                      <span class="sentiment-value" style="color:#6060a0">—</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    pct = int((score + 1) / 2 * 100)
                    bar_color = "#00e676" if score >= 0.15 else "#ff5252" if score <= -0.15 else "#ffeb3b"

                    if score >= 0:
                        bar_left  = "50%"
                        bar_width = f"{pct - 50}%"
                    else:
                        bar_left  = f"{pct}%"
                        bar_width = f"{50 - pct}%"

                    st.markdown(f"""
                    <div class="region-row">
                      <span class="region-name" style="color:#00ffc8; font-weight:600;">{country}</span>
                      <div class="sentiment-bar-bg">
                        <div class="sentiment-bar-fill"
                             style="background:{bar_color}; width:{bar_width}; margin-left:{bar_left};"></div>
                      </div>
                      <span class="sentiment-value" style="color:{bar_color}">
                        {'+' if score >= 0 else ''}{score:.2f}
                      </span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_btn:
                if st.button("👉", key=f"country_{country}_btn", help=f"View {country} news & stocks"):
                    st.session_state.selected_region = country
                    st.rerun()

        st.markdown("<div style='margin-bottom:14px'></div>", unsafe_allow_html=True)

    st.divider()

    # ── News Articles ──────────────────────────────────────────────────────────
    selected_region = st.session_state.selected_region

    if selected_region:
        st.markdown(
            f"<div style='display:inline-block; background:linear-gradient(90deg,#00ffc822,#7b61ff22);"
            f" border:1px solid rgba(0,255,200,0.4); color:#00ffc8; padding:3px 14px;"
            f" border-radius:20px; font-size:12px; font-weight:700; text-transform:uppercase;"
            f" letter-spacing:0.05em;'>📍 {selected_region}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"### Headlines · {selected_region}")

        with st.spinner("Fetching regional news…"):
            # TASK 1: Pass current topic to region fetch for relevance
            display_articles = fetch_news_by_region(selected_region, topic=active_topic)

        if display_articles:
            display_articles = analyze_articles(display_articles)
        elif all_articles:
            # TASK 2: Fallback — show topic articles tagged to this region
            display_articles = [a for a in all_articles if a.get("region") == selected_region]
            if not display_articles:
                st.info(f"No articles found specifically for {selected_region}. Showing global headlines.")
                display_articles = all_articles[:5]
    else:
        st.markdown(f"### 📰 Headlines · {active_topic}")
        display_articles = all_articles[:8] if all_articles else []

    if display_articles:
        for article in display_articles:
            title       = article.get("title", "No Title")
            url         = article.get("url", "#")
            description = article.get("description") or ""
            source_name = (article.get("source") or {}).get("name", "Unknown")
            published   = (article.get("publishedAt") or "")[:10]
            region      = article.get("region", "Global")
            sentiment   = article.get("sentiment", 0.0)

            if isinstance(sentiment, dict):
                sentiment = sentiment.get("score", 0.0)

            if sentiment >= 0.15:
                s_class, s_label = "badge-positive", "▲ Positive"
            elif sentiment <= -0.15:
                s_class, s_label = "badge-negative", "▼ Negative"
            else:
                s_class, s_label = "badge-neutral",  "◆ Neutral"

            desc_snippet = description[:200] + ("…" if len(description) > 200 else "") if description else ""

            st.markdown(f"""
            <div class="news-card">
              <div class="badge-row">
                <span class="badge badge-region">{region}</span>
                <span class="badge {s_class}">{s_label} {sentiment:+.2f}</span>
              </div>
              <a href="{url}" target="_blank"
                 style="color:#00ffc8; text-decoration:none; font-weight:600; font-size:14px;
                        line-height:1.4em;">
                {title}
              </a>
              {f'<p style="color:#a0a0c0; font-size:12.5px; margin: 6px 0 4px;">{desc_snippet}</p>' if desc_snippet else ''}
              <span class="news-meta">🗞 {source_name} &nbsp;·&nbsp; 📅 {published}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        if selected_region:
            st.warning(f"No articles found for {selected_region}. Try clicking another region.")
        else:
            st.info("Select a topic above to load global news and sentiment.")

    # ── Country-Specific Stocks ────────────────────────────────────────────────
    COUNTRIES = ["India", "America", "England", "Japan", "China", "Iran"]
    if selected_region and selected_region in COUNTRIES:
        st.markdown("---")
        st.markdown(f"### 📈 {selected_region} Stock Picks")
        st.markdown(
            "<p style='color:#6060a0; font-size:12px; margin-top:-8px;'>"
            f"Top stocks affected by {active_topic} sentiment in {selected_region}</p>",
            unsafe_allow_html=True,
        )

        # Get country-specific sentiment for confidence
        country_sentiment = region_sentiments.get(selected_region, 0.0)
        news_count = len(all_articles)

        with st.spinner(f"Fetching {selected_region} market data…"):
            country_stocks = get_country_stock_suggestions(
                country=selected_region,
                sentiment_score=country_sentiment,
                news_count=news_count,
                max_stocks=6,
            )

        if country_stocks:
            for stock in country_stocks:
                price = stock.get("price")
                change = stock.get("change_pct", 0.0)
                confidence = stock.get("confidence", 50.0)
                error = stock.get("error")
                exchange = stock.get("exchange", "")

                price_str = f"${price:,.2f}" if price else "—"
                if change > 0:
                    change_str = f"▲ {change:+.2f}%"
                    change_class = "stock-change-pos"
                elif change < 0:
                    change_str = f"▼ {change:.2f}%"
                    change_class = "stock-change-neg"
                else:
                    change_str = f"◆ {change:.2f}%"
                    change_class = "stock-change-neu"

                conf_color = (
                    "#00e676" if confidence >= 70 else
                    "#ffeb3b" if confidence >= 50 else
                    "#ff5252"
                )

                st.markdown(f"""
                <div class="stock-card">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                      <div class="stock-ticker">{stock['ticker']}</div>
                      <div class="stock-name">{stock['name']}</div>
                      <div style="font-size:10px; color:#5050a0; margin-top:2px;">{exchange}</div>
                    </div>
                    <div style="text-align:right;">
                      <div class="stock-price">{price_str}</div>
                      <div class="{change_class}">{change_str}</div>
                    </div>
                  </div>
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                    <span style="font-size:10px; color:#6060a0;">Confidence</span>
                    <span style="font-size:11px; font-weight:700; color:{conf_color};">{confidence:.0f}%</span>
                  </div>
                  <div class="confidence-bar-bg">
                    <div class="confidence-bar-fill" style="width:{confidence}%;"></div>
                  </div>
                  {"<div style='font-size:9px; color:#504060; margin-top:4px;'>⚠ Price unavailable (market closed or API limit)</div>" if error else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No stock data available for {selected_region}.")

    st.markdown(
        "<p style='color:#3a3a5a; font-size:11px; margin-top:8px;'>"
        "Powered by NewsAPI · Sentiment: VADER · Stocks: yfinance · Cached 5 min</p>",
        unsafe_allow_html=True,
    )
