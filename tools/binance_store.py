import os
import pandas as pd
import datetime as dt
from backtrader.dataseries import TimeFrame
from backtrader.feeds import GenericCSVData

class BinanceStore(object):
    """
    Store class for handling Binance data, supporting both local CSV files and API data
    """
    _GRANULARITIES = {
        (TimeFrame.Minutes, 1): '1m',
        (TimeFrame.Minutes, 3): '3m',
        (TimeFrame.Minutes, 5): '5m',
        (TimeFrame.Minutes, 15): '15m',
        (TimeFrame.Minutes, 30): '30m',
        (TimeFrame.Minutes, 60): '1h',
        (TimeFrame.Minutes, 120): '2h',
        (TimeFrame.Minutes, 240): '4h',
        (TimeFrame.Minutes, 360): '6h',
        (TimeFrame.Minutes, 480): '8h',
        (TimeFrame.Minutes, 720): '12h',
        (TimeFrame.Days, 1): '1d',
        (TimeFrame.Days, 3): '3d',
        (TimeFrame.Weeks, 1): '1w',
        (TimeFrame.Months, 1): '1M',
    }

    def __init__(self, coin_target='USDT', testnet=False):
        self.coin_target = coin_target
        self.testnet = testnet

    def getdata(self, dataname, timeframe, compression, start_date=None, end_date=None, LiveBars=False):
        """Get data from API (not implemented as we're focusing on local data)"""
        raise NotImplementedError("API data fetching not implemented - use local data instead")

    def getlocaldata(self, dataname, timeframe, compression, start_date=None, end_date=None, datapath='\\\\znas\\Main\\spot'):
        """
        Get data from local CSV files
        
        Args:
            dataname: Symbol name (e.g., 'BTCUSDT')
            timeframe: Backtrader timeframe
            compression: Data compression factor
            start_date: Start date for data
            end_date: End date for data
            datapath: Base path for local data files
        """
        # Handle date parameters
        if start_date is None:
            start_date = dt.datetime.now() - dt.timedelta(days=30)
        elif isinstance(start_date, str):
            start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
            
        if end_date is None:
            end_date = dt.datetime.now()
        elif isinstance(end_date, str):
            end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
        
        # First try direct file access
        date_str = start_date.strftime('%Y-%m-%d')
        direct_file = os.path.join(datapath, f"{date_str}_{dataname}_1m.csv")
        merged_data = pd.DataFrame()
        
        def process_csv_file(file_path):
            """Helper function to process a CSV file and return a DataFrame"""
            df = pd.read_csv(file_path)
            
            # Handle different datetime column names
            if 'datetime' not in df.columns and 'candle_begin_time' in df.columns:
                print(f"Converting 'candle_begin_time' to 'datetime'")
                df['datetime'] = pd.to_datetime(df['candle_begin_time'])
                df.drop('candle_begin_time', axis=1, inplace=True)
            else:
                df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Verify required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            df.set_index('datetime', inplace=True)
            return df

        # Try direct file access first
        print(f"Trying direct file access: {direct_file}")
        try:
            df = process_csv_file(direct_file)
            merged_data = df
            print(f"Successfully processed {len(df)} rows from direct file")
        except FileNotFoundError:
            print("Direct file not found, trying date-based directory structure...")
            # Fall back to date-based directory structure
            current_date = start_date.date()
            end_date = end_date.date()
            found_data = False
            
            # Collect data from each day's file
            while current_date <= end_date: 
                date_str = current_date.strftime('%Y-%m-%d')
                file_path = os.path.join(datapath, date_str, f"{date_str}_{dataname}_1m.csv")
                
                try:
                    print(f"Processing data file: {file_path}")
                    df = process_csv_file(file_path)
                    merged_data = pd.concat([merged_data, df]) if not merged_data.empty else df
                    found_data = True
                    print(f"Successfully processed {len(df)} rows from {date_str}")
                except FileNotFoundError:
                    print(f"Warning: Data file not found {file_path}")
                except pd.errors.EmptyDataError:
                    print(f"Warning: Empty data file {file_path}")
                except Exception as e:
                    print(f"Error processing {date_str} data: {str(e)}")
                
                current_date += dt.timedelta(days=1)
            
            # If no data found in date directories, try direct file one more time with .csv extension
            if not found_data:
                direct_file_csv = os.path.join(datapath, f"{date_str}_{dataname}.csv")
                try:
                    print(f"Trying direct file access with .csv extension: {direct_file_csv}")
                    df = process_csv_file(direct_file_csv)
                    merged_data = df
                    print(f"Successfully processed {len(df)} rows from direct file")
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    pass
        
        if merged_data.empty:
            raise ValueError(f"No data found between {start_date} and {end_date}")
        
        # Sort and remove duplicates
        merged_data = merged_data.sort_index()
        merged_data = merged_data[~merged_data.index.duplicated(keep='first')]
        
        # Save merged data
        output_dir = os.path.join(datapath, 'merged')
        os.makedirs(output_dir, exist_ok=True)
        
        # Format dates for filename
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, dt.datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, dt.datetime) else end_date
        
        output_path = os.path.join(output_dir, f"{start_str}_{dataname}_1m_{end_str}.csv")
        print(f"Saving merged data to: {output_path}")
        merged_data.to_csv(output_path)
        
        # Create and return a GenericCSVData feed
        data = GenericCSVData(
            dataname=output_path,
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=-1,
            timeframe=timeframe,
            compression=compression,
            headers=True,
            separator=','
        )
        
        return data
