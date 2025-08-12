import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time
import requests
from pytz import timezone
import json

st.set_page_config(page_title="Finance Portfolio Tracker", layout="wide")

# ----------------------------
# Local Storage Functions
# ----------------------------

def load_portfolio():
    """Load portfolio from local storage"""
    try:
        if 'portfolio' in st.session_state:
            return st.session_state.portfolio
        params = st.experimental_get_query_params()
        if 'portfolio' in params:
            return json.loads(params['portfolio'][0])
        return []
    except:
        return []

def save_portfolio(portfolio):
    """Save portfolio to local storage"""
    st.session_state.portfolio = portfolio
    st.experimental_set_query_params(portfolio=json.dumps(portfolio))

# Initialize all session state variables
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_portfolio()
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'fetched_price' not in st.session_state:
    st.session_state.fetched_price = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []

# ----------------------------
# Enhanced Helper Functions
# ----------------------------

def get_ticker_recommendations(query):
    """Get recommended tickers from Yahoo Finance with better reliability"""
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        recommendations = []
        for quote in data.get('quotes', [])[:8]:
            symbol = quote.get('symbol', '')
            name = quote.get('shortname', quote.get('longname', ''))
            exchange = quote.get('exchange', 'Unknown')
            
            if exchange == 'NSE':
                symbol = f"{symbol}"
            elif exchange in ['BSE', 'BOM']:
                symbol = f"{symbol}"
            
            recommendations.append({
                "symbol": symbol,
                "name": name,
                "exchange": exchange
            })
        return recommendations
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def get_historical_price(ticker, date):
    """Get historical price with proper series handling"""
    try:
        date = pd.to_datetime(date)
        end_date = date + timedelta(days=1)
        
        data = yf.download(
            ticker,
            start=date - timedelta(days=7),
            end=end_date,
            progress=False,
            interval="1d"
        )
        
        if not data.empty:
            data = data[data.index <= date]
            if not data.empty:
                return float(data['Close'].iloc[-1])
        return None
    except Exception as e:
        st.error(f"Price fetch error: {str(e)}")
        return None

# ----------------------------
# UI Implementation
# ----------------------------

st.title("📈 Smart Finance Portfolio Tracker")

# Real-time search without Enter key
search_query = st.text_input(
    "Start typing company name or ticker (minimum 3 characters)",
    placeholder="e.g., Reliance, AAPL, TCS",
    key="search_input"
)

# Auto-search when query changes
if search_query and len(search_query) >= 3 and search_query != st.session_state.last_search:
    st.session_state.last_search = search_query
    with st.spinner("🔍 Searching for stocks..."):
        recommendations = get_ticker_recommendations(search_query)
        time.sleep(0.2)
        st.session_state.recommendations = recommendations or []

# Display recommendations if available
if st.session_state.recommendations:
    st.subheader("📌 Matching Stocks")
    
    options = [f"{rec['symbol']} | {rec['name']} ({rec['exchange']})" 
              for rec in st.session_state.recommendations]
    
    selected = st.selectbox("Select a stock:", options, index=0, key="stock_select")
    
    if selected:
        ticker_symbol = selected.split(" | ")[0]
        st.session_state.selected_ticker = ticker_symbol
        
        # Display stock preview
        st.subheader("📊 Stock Preview")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                current_price = info.get('currentPrice', 
                                       ticker.history(period="1d")['Close'].iloc[-1])
                currency = "₹" if ".NS" in ticker_symbol or ".BO" in ticker_symbol else "$"
                st.metric("Current Price", f"{currency}{current_price:.2f}")
                
                st.write(f"**Company:** {info.get('shortName', 'N/A')}")
                st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                st.write(f"**Exchange:** {info.get('exchange', 'N/A')}")
                st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
                
            except Exception as e:
                st.error(f"Couldn't fetch details: {str(e)}")
        
        with col2:
            period = st.selectbox("Chart Period", ["1mo", "3mo", "6mo", "1yr"], index=1)
            try:
                hist_data = ticker.history(period=period)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=hist_data['Close'],
                    mode='lines',
                    line=dict(color='#4B8BBE'),
                    name='Price'
                ))
                fig.update_layout(
                    title=f"{ticker_symbol} Price History",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.warning("Couldn't load price history")

        # Transaction Section
        st.subheader("💵 Add to Portfolio")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quantity = st.number_input("Quantity", min_value=1, value=10, step=1)
        
        with col2:
            buy_date = st.date_input(
                "Purchase Date",
                value=datetime.now() - timedelta(days=30),
                max_value=datetime.now()
            )
            
            # Auto-fetch price when date changes
            if st.session_state.selected_ticker and buy_date:
                with st.spinner("Fetching historical price..."):
                    hist_price = get_historical_price(ticker_symbol, buy_date)
                    if hist_price is not None:
                        st.session_state.fetched_price = hist_price
                        st.success(f"Price on {buy_date}: {currency}{hist_price:.2f}")
        
        with col3:
            buy_price = st.number_input(
                "Price per Share",
                value=st.session_state.get('fetched_price', current_price),
                min_value=0.01,
                step=0.01
            )
        
        if st.button("➕ Add to Portfolio", type="primary"):
            if not ticker_symbol:
                st.error("Please select a valid stock")
            else:
                new_portfolio = st.session_state.portfolio.copy()
                new_portfolio.append({
                    "symbol": ticker_symbol,
                    "name": selected.split(" | ")[1].split(" (")[0],
                    "quantity": quantity,
                    "buy_price": buy_price,
                    "buy_date": buy_date.strftime("%Y-%m-%d"),
                    "current_price": current_price,
                    "exchange": selected.split("(")[1].replace(")", "")
                })
                
                save_portfolio(new_portfolio)
                st.success(f"Added {ticker_symbol} to portfolio!")
                st.balloons()
                time.sleep(1)
                st.rerun()

# Portfolio Display
st.subheader("📊 Your Portfolio")
if st.session_state.portfolio:
    portfolio_df = pd.DataFrame(st.session_state.portfolio)
    
    # Update current prices
    try:
        new_portfolio = []
        for holding in st.session_state.portfolio:
            try:
                ticker = yf.Ticker(holding['symbol'])
                current_price = ticker.history(period="1d")['Close'].iloc[-1]
                updated_holding = holding.copy()
                updated_holding['current_price'] = current_price
                new_portfolio.append(updated_holding)
            except:
                new_portfolio.append(holding)  # Keep old price if can't update
        
        st.session_state.portfolio = new_portfolio
        save_portfolio(new_portfolio)
    except:
        st.warning("Couldn't refresh all current prices")
    
    portfolio_df = pd.DataFrame(st.session_state.portfolio)
    
    # Calculate metrics
    portfolio_df["investment"] = portfolio_df["quantity"] * portfolio_df["buy_price"]
    portfolio_df["current_value"] = portfolio_df["quantity"] * portfolio_df["current_price"]
    portfolio_df["pnl"] = portfolio_df["current_value"] - portfolio_df["investment"]
    portfolio_df["pnl_pct"] = (portfolio_df["pnl"] / portfolio_df["investment"]) * 100
    
    # Display portfolio with delete buttons
    st.dataframe(
        portfolio_df.style.format({
            "buy_price": "{:.2f}",
            "current_price": "{:.2f}",
            "investment": "{:.2f}",
            "current_value": "{:.2f}",
            "pnl": "{:.2f}",
            "pnl_pct": "{:.2f}%"
        }),
        use_container_width=True,
        height=400
    )
    
    # Add delete functionality
    st.subheader("🗑️ Manage Portfolio")
    if st.session_state.portfolio:
        delete_index = st.selectbox(
            "Select stock to remove",
            options=[f"{i+1}. {item['symbol']} - {item['name']} (Qty: {item['quantity']})" 
                    for i, item in enumerate(st.session_state.portfolio)],
            index=0,
            key="delete_select"
        )
        
        if st.button("❌ Remove Selected Stock", type="secondary"):
            selected_index = int(delete_index.split(".")[0]) - 1
            if 0 <= selected_index < len(st.session_state.portfolio):
                removed_stock = st.session_state.portfolio[selected_index]
                new_portfolio = [item for i, item in enumerate(st.session_state.portfolio) 
                               if i != selected_index]
                save_portfolio(new_portfolio)
                st.success(f"Removed {removed_stock['symbol']} from portfolio!")
                time.sleep(1)
                st.rerun()
    
    # Portfolio analytics
    st.subheader("📈 Portfolio Analytics")
    tab1, tab2 = st.tabs(["Performance", "Allocation"])
    
    with tab1:
        selected = st.selectbox(
            "Select stock to analyze",
            portfolio_df["symbol"].unique(),
            key="analysis_select"
        )
        
        stock_data = portfolio_df[portfolio_df["symbol"] == selected].iloc[0]
        hist = yf.Ticker(selected).history(period="1y")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            name="Price History"
        ))
        
        # Convert buy_date to datetime and remove timezone for Plotly compatibility
        buy_date = pd.to_datetime(stock_data['buy_date']).to_pydatetime()
        fig.add_vline(
            x=buy_date.timestamp(),
            line_dash="dash",
            line_color="red",
            annotation_text="Your Purchase",
            annotation_position="top left",
            annotation=None
        )
        
        fig.update_layout(title=f"{selected} Performance", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = go.Figure(go.Pie(
            labels=portfolio_df["symbol"] + " (" + portfolio_df["name"] + ")",
            values=portfolio_df["current_value"],
            hole=0.3
        ))
        fig.update_layout(title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Your portfolio is empty. Search for stocks above to get started.")

# Add a clear all button at the bottom
if st.session_state.portfolio:
    if st.button("🧹 Clear Entire Portfolio", type="primary"):
        save_portfolio([])
        st.success("Portfolio cleared successfully!")
        time.sleep(1)
        st.rerun()
