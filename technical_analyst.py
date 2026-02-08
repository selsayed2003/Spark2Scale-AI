import pandas as pd
import pandas_ta as ta
import os

def calculate_technical_indicators(input_file: str):
    """
    Calculates SMA (Trend) and RSI (Momentum) indicators.
    
    Args:
        input_file (str): Path to the raw CSV from Tool 1.
        
    Returns:
        str: Path to the new CSV with indicators added.
    """
    print(f"\n📈 [Tool 2] Calculating indicators...")
    try:
        if not os.path.exists(input_file):
            print("❌ Error: Input file not found.")
            return None
            
        df = pd.read_csv(input_file)
        
        # Calculate Simple Moving Average (20-day trend)
        df['SMA_20'] = ta.sma(df['close'], length=20)
        
        # Calculate RSI (14-day momentum)
        df['RSI_14'] = ta.rsi(df['close'], length=14)
        
        # Drop rows with NaN (created by calculation lag)
        df.dropna(inplace=True)
        
        # Save Output
        output_file = input_file.replace(".csv", "_analyzed.csv")
        df.to_csv(output_file, index=False)
        
        print(f"✅ Success: Added SMA and RSI columns.")
        return output_file

    except Exception as e:
        print(f"⚠️ Math Error: {e}")
        return None