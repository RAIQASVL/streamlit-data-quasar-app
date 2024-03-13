import os
from dotenv import load_dotenv
import quandl
from alpha_vantage.timeseries import TimeSeries

dotenv_path = "api_keys.env"
load_dotenv(dotenv_path)

quandl.ApiConfig.api_key = os.environ.get("YOUR_QUANDL_API_KEY")
ts = TimeSeries(
    key=os.environ.get("YOUR_ALPHA_VANTAGE_API_KEY"), output_format="pandas"
)

alpha_vantage_key = os.environ.get("YOUR_ALPHA_VANTAGE_API_KEY")
quandl_key = os.environ.get("YOUR_QUANDL_API_KEY")

print("Alpha Vantage API Key:", alpha_vantage_key)
print("Quandl API Key:", quandl_key)

ticker = "MSFT"  # or any default value
start_date = "2022-01-01"  # or any default value
end_date = "2022-12-31"  # or any default value

price_meta_data = None

try:
    price_data, price_meta_data = ts.get_daily(symbol=ticker, outputsize="full")
    print("Alpha Vantage API Response (Price Data):", price_data)
except Exception as e:
    print("Alpha Vantage API Error (Price Data):", e)

try:
    treasury_yield = quandl.get("FRED/TB3MS", start_date=start_date, end_date=end_date)
    print("Quandl API Response (Treasury Yield):", treasury_yield)
except Exception as e:
    print("Quandl API Error (Treasury Yield):", e)

# Alpha Vantage
if price_meta_data and "Error Message" not in price_meta_data:
    print("Alpha Vantage API Request Successful")
else:
    print("Alpha Vantage API Request Failed")

# Quandl
if not treasury_yield.empty:
    print("Quandl API Request Successful")
else:
    print("Quandl API Request Failed")
