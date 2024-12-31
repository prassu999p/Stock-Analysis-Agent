import streamlit as st
import yfinance as yf
import pandas as pd
import time
import google.generativeai as genai
from duckduckgo_search import DDGS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Google Gemini LLM
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Streamlit App
st.title("Stock Analysis App")

# User Input
st.sidebar.header("User Input")
market = st.sidebar.selectbox("Select Market:", ["USA", "Singapore", "India (NSE)", "India (BSE)"])
stock_ticker = st.sidebar.text_input(f"Enter Stock Ticker for {market} (e.g., {'AAPL' if market == 'USA' else 'D05.SI' if market == 'Singapore' else 'RELIANCE.NS' if market == 'India (NSE)' else 'RELIANCE.BO'}):")

# Adjust ticker based on market
if market == "Singapore":
    if not stock_ticker.endswith(".SI"):
        stock_ticker += ".SI"
elif market == "India (NSE)":
    if not stock_ticker.endswith(".NS"):
        stock_ticker += ".NS"
elif market == "India (BSE)":
    if not stock_ticker.endswith(".BO"):
        stock_ticker += ".BO"

# Fetch Stock Data
@st.cache_resource  # Use st.cache_resource for non-serializable objects
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock

stock = get_stock_data(stock_ticker)
info = stock.info

# Display Stock Info with Fundamentals
st.header(f"Stock Information for {stock_ticker}")

# Create a table with basic info on the left and fundamentals on the right
col1, col2 = st.columns(2)

# Left Column: Basic Stock Info
with col1:
    st.write("### Basic Information")
    st.write(f"**Company Name:** {info.get('longName', 'N/A')}")
    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
    st.write(f"**Industry:** {info.get('industry', 'N/A')}")
    st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
    st.write(f"**Current Price:** {info.get('currentPrice', 'N/A')}")

# Right Column: Fundamentals
with col2:
    st.write("### Fundamentals")
    st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
    st.write(f"**EPS:** {info.get('trailingEps', 'N/A')}")
    st.write(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")
    st.write(f"**Revenue Growth:** {info.get('revenueGrowth', 'N/A')}")
    st.write(f"**Profit Margins:** {info.get('profitMargins', 'N/A')}")
    st.write(f"**Debt to Equity:** {info.get('debtToEquity', 'N/A')}")

# Create Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Sentiment Analysis", "News", "Technical"])

# Summary Tab
with tab1:
    st.header("Summary and Analyst Recommendations")
    with st.spinner("Generating summary and recommendations..."):
        # Fetch analyst recommendations
        recommendations = stock.recommendations
        if recommendations is not None and not recommendations.empty:
            st.write("### Analyst Recommendations")
            st.dataframe(recommendations.tail(5))  # Show latest 5 recommendations

        # Fetch stock data for the summary
        hist = stock.history(period="1y")
        current_price = info.get('currentPrice', 'N/A')
        market_cap = info.get('marketCap', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        dividend_yield = info.get('dividendYield', 'N/A')

        # Generate a quick summary using Gemini
        prompt = f"""
        Provide a quick summary for the stock {stock_ticker} based on the following data:
        - Current Price: {current_price}
        - Market Cap: {market_cap}
        - P/E Ratio: {pe_ratio}
        - Dividend Yield: {dividend_yield}
        - Historical Prices (1 year): {hist['Close'].tolist()}
        - Analyst Recommendations: {recommendations.tail(5).to_dict() if recommendations is not None else 'N/A'}
        """
        response = model.generate_content(prompt)
        st.write("### Quick Summary")
        st.write(response.text)

# Sentiment Analysis Tab
with tab2:
    st.header("Sentiment Analysis")
    with st.spinner("Analyzing sentiment..."):
        # Fetch recent news and data for sentiment analysis
        ddgs = DDGS()
        news_articles = ddgs.text(f"{stock_ticker} stock news", max_results=5)
        news_summary = "\n".join([f"{article['title']}: {article['body']}" for article in news_articles])

        # Fetch stock data for sentiment analysis
        hist = stock.history(period="1y")
        current_price = info.get('currentPrice', 'N/A')
        market_cap = info.get('marketCap', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        dividend_yield = info.get('dividendYield', 'N/A')

        # Generate sentiment analysis using Gemini
        sentiment_prompt = f"""
        Analyze the sentiment for the stock {stock_ticker} based on the following data:
        - Current Price: {current_price}
        - Market Cap: {market_cap}
        - P/E Ratio: {pe_ratio}
        - Dividend Yield: {dividend_yield}
        - Historical Prices (1 year): {hist['Close'].tolist()}
        - Recent News: {news_summary}

        Provide the output in the following format:
        ### Overall Sentiment
        [Overall sentiment summary]

        ### Positive Sentiments
        [List of positive aspects]

        ### Negative Sentiments
        [List of negative aspects]
        """
        sentiment_response = model.generate_content(sentiment_prompt)

        # Display the overall sentiment
        st.write("### Overall Sentiment")
        st.write(sentiment_response.text.split("### Positive Sentiments")[0].strip())

        # Display positive sentiments in an expandable section
        with st.expander("Positive Sentiments"):
            positive_sentiments = sentiment_response.text.split("### Positive Sentiments")[1].split("### Negative Sentiments")[0].strip()
            st.write(positive_sentiments)

        # Display negative sentiments in an expandable section
        with st.expander("Negative Sentiments"):
            negative_sentiments = sentiment_response.text.split("### Negative Sentiments")[1].strip()
            st.write(negative_sentiments)

# News Tab
with tab3:
    st.header("Recent News")
    with st.spinner("Fetching news..."):
        ddgs = DDGS()
        news_articles = ddgs.text(f"{stock_ticker} stock news", max_results=5)
        if news_articles:
            st.write("### News Articles")
            for i, article in enumerate(news_articles):
                st.write(f"#### {i + 1}. {article['title']}")
                st.write(f"**Source:** {article.get('source', 'N/A')}")
                st.write(f"**Link:** [Read more]({article.get('link', '#')})")
                st.write(f"**Snippet:** {article.get('body', 'N/A')}")
                st.write("---")
        else:
            st.write("No recent news articles found.")

# Technical Analysis Tab
with tab4:
    st.header("Technical Analysis")
    hist = stock.history(period="1y")
    st.write("### Historical Prices")
    st.line_chart(hist['Close'])

    st.write("### Moving Averages")
    st.write("**50-Day Moving Average:**", hist['Close'].rolling(window=50).mean().iloc[-1])
    st.write("**200-Day Moving Average:**", hist['Close'].rolling(window=200).mean().iloc[-1])