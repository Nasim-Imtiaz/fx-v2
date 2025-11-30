import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class IchimokuCalculator:
    """Calculate Ichimoku Cloud indicators"""
    
    def __init__(self, tenkan_period=9, kijun_period=26, senkou_b_period=52, chikou_shift=26):
        """
        Initialize Ichimoku calculator
        
        Args:
            tenkan_period: Period for Tenkan-sen (Conversion Line), default 9
            kijun_period: Period for Kijun-sen (Base Line), default 26
            senkou_b_period: Period for Senkou Span B, default 52
            chikou_shift: Shift for Chikou Span (Lagging Span), default 26
        """
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.chikou_shift = chikou_shift
    
    def calculate(self, df):
        """
        Calculate all Ichimoku components
        
        Args:
            df: DataFrame with columns: 'high', 'low', 'close', 'time'
        
        Returns:
            DataFrame with Ichimoku indicators added
        """
        if df is None or len(df) == 0:
            return None
        
        # Make a copy to avoid modifying original
        result_df = df.copy()
        
        # Calculate Tenkan-sen (Conversion Line)
        # (9-period high + 9-period low) / 2
        tenkan_high = result_df['high'].rolling(window=self.tenkan_period).max()
        tenkan_low = result_df['low'].rolling(window=self.tenkan_period).min()
        result_df['tenkan_sen'] = (tenkan_high + tenkan_low) / 2
        
        # Calculate Kijun-sen (Base Line)
        # (26-period high + 26-period low) / 2
        kijun_high = result_df['high'].rolling(window=self.kijun_period).max()
        kijun_low = result_df['low'].rolling(window=self.kijun_period).min()
        result_df['kijun_sen'] = (kijun_high + kijun_low) / 2
        
        # Calculate Senkou Span A (Leading Span A)
        # (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
        result_df['senkou_span_a'] = (result_df['tenkan_sen'] + result_df['kijun_sen']) / 2
        # Shift forward by 26 periods
        result_df['senkou_span_a'] = result_df['senkou_span_a'].shift(-self.chikou_shift)
        
        # Calculate Senkou Span B (Leading Span B)
        # (52-period high + 52-period low) / 2, plotted 26 periods ahead
        senkou_b_high = result_df['high'].rolling(window=self.senkou_b_period).max()
        senkou_b_low = result_df['low'].rolling(window=self.senkou_b_period).min()
        result_df['senkou_span_b'] = (senkou_b_high + senkou_b_low) / 2
        # Shift forward by 26 periods
        result_df['senkou_span_b'] = result_df['senkou_span_b'].shift(-self.chikou_shift)
        
        # Calculate Chikou Span (Lagging Span)
        # Current closing price, plotted 26 periods back
        result_df['chikou_span'] = result_df['close'].shift(self.chikou_shift)
        
        return result_df
    
    def get_cloud_status(self, row):
        """
        Determine if price is above or below the cloud
        
        Args:
            row: DataFrame row with senkou_span_a and senkou_span_b
        
        Returns:
            str: 'above', 'below', or 'inside' (if spans are NaN)
        """
        span_a = row.get('senkou_span_a')
        span_b = row.get('senkou_span_b')
        price = row.get('close')
        
        if pd.isna(span_a) or pd.isna(span_b) or pd.isna(price):
            return None
        
        # Cloud top is the higher of the two spans
        cloud_top = max(span_a, span_b)
        # Cloud bottom is the lower of the two spans
        cloud_bottom = min(span_a, span_b)
        
        if price > cloud_top:
            return 'above'
        elif price < cloud_bottom:
            return 'below'
        else:
            return 'inside'
    
    def generate_signal(self, row, previous_row=None):
        """
        Generate trading signal based on Ichimoku conditions
        
        Buy signal conditions:
        - Price is above the cloud
        - Base line (Kijun-sen) is above conversion line (Tenkan-sen)
        - Lagging span (Chikou) is above price
        
        Sell signal conditions:
        - Price is below the cloud
        - Base line (Kijun-sen) is below conversion line (Tenkan-sen)
        - Lagging span (Chikou) is below price
        
        Args:
            row: Current DataFrame row with Ichimoku indicators
            previous_row: Previous row (optional, for trend confirmation)
        
        Returns:
            dict: Signal information with 'signal' ('buy', 'sell', or 'neutral') and conditions
        """
        # Check if we have all required values
        required_fields = ['close', 'tenkan_sen', 'kijun_sen', 'chikou_span', 
                          'senkou_span_a', 'senkou_span_b']
        
        for field in required_fields:
            if field not in row or pd.isna(row[field]):
                return {
                    'signal': 'neutral',
                    'reason': f'Missing or NaN value for {field}',
                    'conditions_met': {}
                }
        
        price = row['close']
        tenkan = row['tenkan_sen']
        kijun = row['kijun_sen']
        chikou = row['chikou_span']
        
        # Get cloud status
        cloud_status = self.get_cloud_status(row)
        
        # Check conditions
        conditions = {
            'price_above_cloud': cloud_status == 'above',
            'price_below_cloud': cloud_status == 'below',
            'kijun_above_tenkan': kijun > tenkan,
            'kijun_below_tenkan': kijun < tenkan,
            'chikou_above_price': chikou > price,
            'chikou_below_price': chikou < price
        }
        
        # Buy signal conditions
        buy_conditions = (
            conditions['price_above_cloud'] and
            conditions['kijun_above_tenkan'] and
            conditions['chikou_above_price']
        )
        
        # Sell signal conditions
        sell_conditions = (
            conditions['price_below_cloud'] and
            conditions['kijun_below_tenkan'] and
            conditions['chikou_below_price']
        )
        
        if buy_conditions:
            return {
                'signal': 'buy',
                'reason': 'Price above cloud, Kijun above Tenkan, Chikou above price',
                'conditions_met': conditions
            }
        elif sell_conditions:
            return {
                'signal': 'sell',
                'reason': 'Price below cloud, Kijun below Tenkan, Chikou below price',
                'conditions_met': conditions
            }
        else:
            return {
                'signal': 'neutral',
                'reason': 'Ichimoku conditions not fully met',
                'conditions_met': conditions
            }
    
    def calculate_with_signals(self, quotes_data):
        """
        Calculate Ichimoku indicators and generate signals for all candles
        
        Args:
            quotes_data: List of quote dictionaries with 'time', 'open', 'high', 'low', 'close'
        
        Returns:
            List of dictionaries with quotes, Ichimoku indicators, and signals
        """
        if not quotes_data or len(quotes_data) == 0:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(quotes_data)
        
        # Ensure we have the required columns
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns. Expected: {required_cols}")
            return []
        
        # Calculate Ichimoku indicators
        df_with_ichimoku = self.calculate(df)
        
        if df_with_ichimoku is None:
            return []
        
        # Reset index to ensure proper integer indexing
        df_with_ichimoku = df_with_ichimoku.reset_index(drop=True)
        
        # Convert back to list of dictionaries with indicators and signals
        result = []
        for idx, row in df_with_ichimoku.iterrows():
            # Get time from original quotes_data if available, otherwise from row
            time_value = None
            if idx < len(quotes_data) and 'time' in quotes_data[idx]:
                time_value = quotes_data[idx]['time']
            elif 'time' in row:
                time_value = row['time']
            
            candle_data = {
                'time': time_value,
                'open': float(row['open']) if 'open' in row and not pd.isna(row['open']) else None,
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            }
            
            # Add Ichimoku indicators (convert NaN to None for JSON serialization)
            ichimoku_data = {
                'tenkan_sen': float(row['tenkan_sen']) if not pd.isna(row['tenkan_sen']) else None,
                'kijun_sen': float(row['kijun_sen']) if not pd.isna(row['kijun_sen']) else None,
                'senkou_span_a': float(row['senkou_span_a']) if not pd.isna(row['senkou_span_a']) else None,
                'senkou_span_b': float(row['senkou_span_b']) if not pd.isna(row['senkou_span_b']) else None,
                'chikou_span': float(row['chikou_span']) if not pd.isna(row['chikou_span']) else None,
            }
            
            # Get cloud status
            cloud_status = self.get_cloud_status(row)
            ichimoku_data['cloud_status'] = cloud_status
            
            # Generate signal
            previous_row = df_with_ichimoku.iloc[idx - 1] if idx > 0 else None
            signal_data = self.generate_signal(row, previous_row)
            
            result.append({
                **candle_data,
                'ichimoku': ichimoku_data,
                'signal': signal_data
            })
        
        return result

