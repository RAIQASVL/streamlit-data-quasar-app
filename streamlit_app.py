import streamlit as st
import os
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime
import quandl
import pandas as pd
import json

# Load environment variables from the .env file
dotenv_path = "api_keys.env"
load_dotenv(dotenv_path)

# Load API keys
ts = TimeSeries(
    key=os.environ.get("YOUR_ALPHA_VANTAGE_API_KEY"), output_format="pandas"
)

# Read SEC registered companies from JSON file
with open("company_tickers.json", "r") as file:
    company_tickers = json.load(file)

# Adding API keys
quandl.ApiConfig.api_key = os.environ.get("YOUR_QUANDL_API_KEY")

# Sidebar inputs for selecting ticker and date range
st.markdown(
    f"Demo app showing **Closing price** and daily **APR change** of a selected ticker from Alpha Vantage API"
)
ticker_options = [
    company_tickers[ticker]["ticker"] for ticker in company_tickers
]  # Change made here
selected_ticker = st.sidebar.selectbox("Select a Company", ticker_options)
selected_company_name = next(
    data["title"]
    for data in company_tickers.values()
    if data["ticker"] == selected_ticker
)  # Change made here
end_date = st.sidebar.date_input("End Date", value=datetime.now()).strftime("%Y/%m/%d")
start_date = st.sidebar.date_input("Start Date", value=datetime(2015, 5, 31)).strftime(
    "%Y/%m/%d"
)

# Convert start and end dates to pandas Timestamp objects
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)


# Function to fetch daily ticker data
@st.cache_data
def get_ticker_daily(ticker_input):
    try:
        ticker_data, ticker_metadata = ts.get_daily(
            symbol=ticker_input, outputsize="full"
        )
        # Init ticker_df
        ticker_df = pd.DataFrame(ticker_data)
        return ticker_df, ticker_metadata
    except Exception as e:
        st.error(f"Error fetching data for {ticker_input}: {str(e)}")
        return None, None


# Fetch ticker data
price_data, price_meta_data = get_ticker_daily(selected_ticker)

if price_data is None:
    st.warning(
        f"No data available for {selected_company_name}. Please choose another ticker or period."
    )
else:
    ticker_df, _ = get_ticker_daily(selected_ticker)  # Initialize ticker_df here
    # Fetch market data (e.g., S&P 500)
    try:
        market_data, market_meta_data = get_ticker_daily("SPY")
        md_chart_1 = f"Price of **{selected_company_name}**"
        md_chart_2 = f"APR daily change of **{selected_company_name}**"
    except:
        market_data, market_meta_data = get_ticker_daily("MSFT")
        md_chart_1 = (
            f"Invalid ticker **{selected_company_name}** showing **MSFT** price"
        )
        md_chart_2 = f"Invalid ticker **{selected_company_name}** showing **MSFT** APR daily change"

    # Calculate APR change
    def apr_change(pandas_series_input):
        return (
            (
                (
                    pandas_series_input
                    - pandas_series_input.shift(periods=-1, fill_value=0)
                )
                / pandas_series_input
            )
            * 100
            * 252
        )

    # Calculate APR change for ticker and market data
    price_data["change"] = apr_change(price_data["4. close"])
    market_data["change"] = apr_change(market_data["4. close"])

    # Sort market data
    market_data = market_data.sort_index()

    # Filter data based on selected date range
    price_data.sort_index(inplace=True)
    price_data_filtered = price_data.loc[end_date:start_date]
    market_data_filtered = market_data[end_date:start_date]
    stock_market_correlation = price_data_filtered["change"].corr(
        market_data_filtered["change"], method="pearson"
    )

    # Estimate risk-free return via 3 months treasury bonds
    treasury_yield = quandl.get("FRED/TB3MS", start_date=start_date, end_date=end_date)
    rfr = treasury_yield["Value"].mean()  # mean treasury yield over the period

    # Calculate metrics
    stock_volatility = price_data_filtered["change"].std()
    market_volatility = market_data_filtered["change"].std()
    stock_excess_return = price_data_filtered["change"].mean() - rfr
    market_excess_return = market_data_filtered["change"].mean() - rfr
    beta = stock_market_correlation * stock_volatility / market_volatility
    alpha = stock_excess_return - beta * market_excess_return
    sharpe = stock_excess_return / stock_volatility
    metrics_df = pd.DataFrame(
        data={
            "Mkt Correlation": [stock_market_correlation],
            "Alpha": [alpha],
            "Beta": [beta],
            "Sharpe Ratio": [sharpe],
        }
    )
    metrics_df.index = [selected_company_name]

    # Display closing price and APR change charts
    st.markdown(md_chart_1)
    st.line_chart(price_data_filtered["4. close"])
    st.markdown(md_chart_2)
    st.line_chart(price_data_filtered["change"])

    # Display metrics table
    st.table(metrics_df)

    # Display raw price data
    st.write("Price Data:", price_data)
