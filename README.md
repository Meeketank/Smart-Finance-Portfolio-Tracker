# Smart-Finance-Portfolio-Tracker

A smart web application built with Streamlit that helps you track your stock portfolio with real-time data visualization and performance analytics.

Features:

Portfolio Management: Add, view, and delete stock holdings

Real-time Data: Fetches current market prices using Yahoo Finance API

Historical Analysis: View purchase price vs current performance

Interactive Charts: Visualize portfolio allocation and stock trends

Persistent Storage: Portfolio saved in browser URL (no database needed)

Stock Search: Intelligent ticker symbol lookup with recommendations

Quick Start:

Clone the repository: git clone https://github.com/yourusername/finance-portfolio-tracker.git

Install dependencies: pip install -r requirements.txt

Run the app: streamlit run finance.py

Access the app at http://localhost:8501

Requirements: Python 3.8+, Streamlit, yfinance, pandas, plotly, requests

How It Works:
The application uses Yahoo Finance API to fetch market data, processes it with pandas, and displays interactive visualizations using Plotly. Portfolio data persists through browser URL parameters.

Project Structure:

finance.py - Main application code

README.md - Documentation

requirements.txt - Dependency list

assets/ - Folder for screenshots

License: MIT License
