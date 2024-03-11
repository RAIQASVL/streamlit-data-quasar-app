import os
from dotenv import load_dotenv

# Load environment variables from a file
dotenv_path = "api_keys.env"
load_dotenv(dotenv_path)

# Import necessary libraries
import streamlit as st
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime
import quandl
import pandas as pd

# Set up Quandl API key and Alpha Vantage time series object
quandl.ApiConfig.api_key = os.environ.get("YOUR_QUANDL_API_KEY")
ts = TimeSeries(
    key=os.environ.get("YOUR_ALPHA_VANTAGE_API_KEY"), output_format="pandas"
)

# Check if the Quandl API key was successfully loaded
if not quandl.ApiConfig.api_key:
    st.error(
        "Failed to load Quandl API key. Please ensure that the environment variable is set."
    )

# Set up Streamlit app
st.markdown(
    f"Demo app showing **Closing price** and daily **APR change** of a selected ticker from Alpha Vantage API"
)

# Get user input for ticker and date range
ticker = st.sidebar.text_input("Ticker", "MSFT").upper()
end_date = st.sidebar.date_input("End date", value=datetime.now()).strftime("%Y/%m/%d")
start_date = st.sidebar.date_input("Start date", value=datetime(2015, 5, 31)).strftime(
    "%Y/%m/%d"
)
start_date = pd.to_datetime(start_date)


# Function to retrieve daily ticker data
@st.cache(allow_output_mutation=True)
def get_ticker_daily(ticker_input):
    ticker_data, ticker_metadata = ts.get_daily(symbol=ticker_input, outputsize="full")
    return ticker_data, ticker_metadata


# Attempt to get data for the selected ticker; if unsuccessful, default to MSFT
try:
    price_data, price_meta_data = get_ticker_daily(ticker)
    market_data, market_meta_data = get_ticker_daily("SPY")
    md_chart_1 = f"Price of **{ticker}**"
    md_chart_2 = f"APR daily change of **{ticker}**"
except:
    price_data, price_meta_data = get_ticker_daily("MSFT")
    market_data, market_meta_data = get_ticker_daily("SPY")
    md_chart_1 = f"Invalid ticker **{ticker}** showing **MSFT** price"
    md_chart_2 = f"Invalid ticker **{ticker}** showing **MSFT** APR daily change"


# Function to calculate APR change
def apr_change(pandas_series_input):
    return (
        (
            (pandas_series_input - pandas_series_input.shift(periods=-1, fill_value=0))
            / pandas_series_input
        )
        * 100
        * 252
    )


# Apply APR change function to price and market data
price_data["change"] = apr_change(price_data["4. close"])
market_data["change"] = apr_change(market_data["4. close"])

# Sort data by index
market_data = market_data.sort_index()
price_data.sort_index(inplace=True)

# Filter data based on date range
price_data_filtered = price_data.loc[end_date:start_date]
market_data_filtered = market_data[end_date:start_date]

# Calculate stock-market correlation
stock_market_correlation = price_data_filtered["change"].corr(
    market_data_filtered["change"], method="pearson"
)

# Convert date strings to datetime objects
end_date = pd.to_datetime(end_date)
start_date = pd.to_datetime(start_date)

# Estimate risk-free return via 3 months treasury bonds
treasury_yield = quandl.get("FRED/TB3MS", start_date=start_date, end_date=end_date)
rfr = treasury_yield["Value"].mean()  # mean treasury yield over the period

# Calculate volatility, excess returns, beta, alpha, and Sharpe ratio
stock_volatility = price_data_filtered["change"].std()
market_volatility = market_data_filtered["change"].std()
stock_excess_return = price_data_filtered["change"].mean() - rfr
market_excess_return = market_data_filtered["change"].mean() - rfr
beta = stock_market_correlation * stock_volatility / market_volatility
alpha = stock_excess_return - beta * market_excess_return
sharpe = stock_excess_return / stock_volatility

# Create a DataFrame with calculated metrics
metrics_df = pd.DataFrame(
    data={
        "mkt correlation": [stock_market_correlation],
        "alpha": [alpha],
        "beta": [beta],
        "Sharp ratio": [sharpe],
    }
)
metrics_df.index = [ticker]

# Display charts and metrics in Streamlit app
st.markdown(md_chart_1)
st.line_chart(price_data_filtered["4. close"])
st.markdown(md_chart_2)
st.line_chart(price_data_filtered["change"])

st.table(metrics_df)
