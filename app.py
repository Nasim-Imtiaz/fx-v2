from flask import Flask, jsonify, request
from metatrader_connector import MetaTraderConnector
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MetaTrader connector
mt_connector = MetaTraderConnector()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'mt_connected': mt_connector.is_connected()})


@app.route('/quotes', methods=['GET'])
def get_quotes():
    """
    Get quotes data from MetaTrader
    
    Query parameters:
    - symbol: Currency pair (e.g., 'EURUSD', 'GBPUSD')
    - timeframe: Timeframe for quotes (e.g., 'M1', 'M5', 'M15', 'H1', 'D1')
    - count: Number of bars to retrieve (default: 100)
    - start_date: Start date in format 'YYYY-MM-DD' (optional)
    - end_date: End date in format 'YYYY-MM-DD' (optional)
    """
    try:
        # Get query parameters
        symbol = request.args.get('symbol', type=str)
        timeframe = request.args.get('timeframe', type=str, default='H1')
        count = request.args.get('count', type=int, default=100)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        
        # Validate required parameters
        if not symbol:
            return jsonify({'error': 'symbol parameter is required'}), 400
        
        # Get quotes from MetaTrader
        quotes_data = mt_connector.get_quotes(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            start_date=start_date,
            end_date=end_date
        )
        
        if quotes_data is None:
            return jsonify({'error': 'Failed to retrieve quotes data'}), 500
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'count': len(quotes_data),
            'data': quotes_data
        })
        
    except Exception as e:
        logger.error(f"Error getting quotes: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/symbols', methods=['GET'])
def get_symbols():
    """Get list of available symbols from MetaTrader"""
    try:
        symbols = mt_connector.get_symbols()
        if symbols is None:
            return jsonify({'error': 'Failed to retrieve symbols'}), 500
        return jsonify({'symbols': symbols})
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize MetaTrader connection
    if not mt_connector.initialize():
        logger.warning("MetaTrader connection failed. Some endpoints may not work.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

