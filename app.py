import streamlit as st
import yfinance as yf
import pandas as pd
import time
import google.generativeai as genai
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
stock_ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL):", "AAPL")

# Fetch Stock Data
@st.cache_resource  # Use st.cache_resource for non-serializable objects
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock

stock = get_stock_data(stock_ticker)
info = stock.info

# Display Stock Info
st.header(f"Stock Information for {stock_ticker}")
st.write(f"**Company Name:** {info.get('longName', 'N/A')}")
st.write(f"**Sector:** {info.get('sector', 'N/A')}")
st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
st.write(f"**Current Price:** {info.get('currentPrice', 'N/A')}")

# Create Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Fundamental", "Technical", "Sentimental", "Summary"])

# Fundamental Analysis Tab
with tab1:
    st.header("Fundamental Analysis")
    st.write("**P/E Ratio:**", info.get('trailingPE', 'N/A'))
    st.write("**EPS:**", info.get('trailingEps', 'N/A'))
    st.write("**Dividend Yield:**", info.get('dividendYield', 'N/A'))
    st.write("**Revenue Growth:**", info.get('revenueGrowth', 'N/A'))

# Technical Analysis Tab
with tab2:
    st.header("Technical Analysis")
    hist = stock.history(period="1y")
    st.write("**50-Day Moving Average:**", hist['Close'].rolling(window=50).mean().iloc[-1])
    st.write("**200-Day Moving Average:**", hist['Close'].rolling(window=200).mean().iloc[-1])
    st.line_chart(hist['Close'])

# Sentimental Analysis Tab
with tab3:
    st.header("Sentimental Analysis")
    with st.spinner("Analyzing sentiment..."):
        prompt = f"Generate a sentimental analysis for the stock {stock_ticker} based on recent market trends and news."
        response = model.generate_content(prompt)
        st.write(response.text)

# Summary Tab
with tab4:
    st.header("Summary and Analyst Recommendations")
    with st.spinner("Generating summary and recommendations..."):
        prompt = f"Provide a summary and analyst recommendations for the stock {stock_ticker}."
        response = model.generate_content(prompt)
        st.write(response.text)
