import yfinance as yf
import pandas as pd
import os

def fetch_stock_data(ticker_symbol: str, period: str = "2y"):
    """
    Fetches historical stock data for a given ticker.
    
    Args:
        ticker_symbol (str): The stock ticker (e.g., 'AAPL').
        period (str): Duration of data (default '2y').
        
    Returns:
        str: Path to the saved CSV file, or None if failed.
    """
    print(f"\n📥 [Tool 1] Fetching data for: {ticker_symbol}...")
    try:
        # Initialize Ticker
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period=period, auto_adjust=True)
        
        if df.empty:
            print(f"❌ Error: No data found for symbol '{ticker_symbol}'.")
            return None
        
        # Clean Data
        df.reset_index(inplace=True)
        df.columns = [c.lower() for c in df.columns]
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Save to CSV
        os.makedirs("data_output", exist_ok=True)
        filename = f"data_output/{ticker_symbol}_market_data.csv"
        df.to_csv(filename, index=False)
        
        print(f"✅ Success: Fetched {len(df)} rows.")
        return filename

    except Exception as e:
        print(f"⚠️ Fetch Error: {e}")
        return None