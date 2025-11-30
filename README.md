# Flask MetaTrader Quotes API

A Flask REST API that communicates with MetaTrader5 to retrieve currency quotes data.

## Features

- GET endpoint for retrieving quotes data based on currency pair and timeframe
- Support for multiple timeframes (M1, M5, M15, H1, D1, etc.)
- Date range filtering for historical data
- List available symbols from MetaTrader
- **Ichimoku Cloud analysis with automated buy/sell signals**
  - Calculates all Ichimoku components (Tenkan-sen, Kijun-sen, Senkou Span A/B, Chikou Span)
  - Generates trading signals based on price position relative to cloud and line relationships

## Prerequisites

- Python 3.7+
- MetaTrader5 terminal installed and running
- MetaTrader5 account (demo or live)

## Installation

1. Clone or download this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Configure MetaTrader connection in `.env` file:
```bash
cp .env.example .env
# Edit .env with your MetaTrader credentials if needed
```

## Usage

1. Make sure MetaTrader5 terminal is running and logged in

2. Start the Flask server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### GET /health
Health check endpoint to verify server and MetaTrader connection status.

**Response:**
```json
{
  "status": "healthy",
  "mt_connected": true
}
```

### GET /quotes
Get quotes data for a currency pair.

**Query Parameters:**
- `symbol` (required): Currency pair symbol (e.g., 'EURUSD', 'GBPUSD')
- `timeframe` (optional): Timeframe for quotes. Default: 'H1'
  - Available: M1, M5, M15, M30, H1, H4, D1, W1, MN1, etc.
- `count` (optional): Number of bars to retrieve. Default: 100
- `start_date` (optional): Start date in 'YYYY-MM-DD' format
- `end_date` (optional): End date in 'YYYY-MM-DD' format

**Example Requests:**
```bash
# Get last 100 hourly quotes for EURUSD
curl "http://localhost:5000/quotes?symbol=EURUSD&timeframe=H1&count=100"

# Get daily quotes for GBPUSD from date range
curl "http://localhost:5000/quotes?symbol=GBPUSD&timeframe=D1&start_date=2024-01-01&end_date=2024-01-31"

# Get 50 M15 quotes for USDJPY
curl "http://localhost:5000/quotes?symbol=USDJPY&timeframe=M15&count=50"
```

**Response:**
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "count": 100,
  "data": [
    {
      "time": "2024-01-15 10:00:00",
      "open": 1.08950,
      "high": 1.09020,
      "low": 1.08910,
      "close": 1.08980,
      "tick_volume": 1234,
      "spread": 2,
      "real_volume": 5678
    },
    ...
  ]
}
```

### GET /symbols
Get list of available symbols from MetaTrader.

**Response:**
```json
{
  "symbols": ["EURUSD", "GBPUSD", "USDJPY", ...]
}
```

### GET /ichimoku
Get hourly candle data with Ichimoku Cloud indicators and trading signals.

**Query Parameters:**
- `symbol` (required): Currency pair symbol (e.g., 'EURUSD', 'GBPUSD')
- `count` (optional): Number of hourly bars to retrieve. Default: 200 (minimum 52 for proper Ichimoku calculation)
- `start_date` (optional): Start date in 'YYYY-MM-DD' format
- `end_date` (optional): End date in 'YYYY-MM-DD' format

**Ichimoku Components:**
- **Tenkan-sen (Conversion Line)**: (9-period high + 9-period low) / 2
- **Kijun-sen (Base Line)**: (26-period high + 26-period low) / 2
- **Senkou Span A (Leading Span A)**: (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
- **Senkou Span B (Leading Span B)**: (52-period high + 52-period low) / 2, plotted 26 periods ahead
- **Chikou Span (Lagging Span)**: Current closing price, plotted 26 periods back

**Trading Signals:**
- **BUY Signal**: Price above cloud, Base Line (Kijun) above Conversion Line (Tenkan), Lagging Span (Chikou) above price
- **SELL Signal**: Price below cloud, Base Line (Kijun) below Conversion Line (Tenkan), Lagging Span (Chikou) below price
- **NEUTRAL**: Conditions not fully met

**Example Request:**
```bash
# Get Ichimoku data for EURUSD
curl "http://localhost:5000/ichimoku?symbol=EURUSD&count=200"
```

**Response:**
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "total_candles": 200,
  "latest_signal": {
    "signal": "buy",
    "reason": "Price above cloud, Kijun above Tenkan, Chikou above price",
    "conditions_met": {
      "price_above_cloud": true,
      "price_below_cloud": false,
      "kijun_above_tenkan": true,
      "kijun_below_tenkan": false,
      "chikou_above_price": true,
      "chikou_below_price": false
    }
  },
  "data": [
    {
      "time": "2024-01-15 10:00:00",
      "open": 1.08950,
      "high": 1.09020,
      "low": 1.08910,
      "close": 1.08980,
      "ichimoku": {
        "tenkan_sen": 1.08960,
        "kijun_sen": 1.08970,
        "senkou_span_a": 1.08965,
        "senkou_span_b": 1.08955,
        "chikou_span": 1.08990,
        "cloud_status": "above"
      },
      "signal": {
        "signal": "buy",
        "reason": "Price above cloud, Kijun above Tenkan, Chikou above price",
        "conditions_met": {
          "price_above_cloud": true,
          "kijun_above_tenkan": true,
          "chikou_above_price": true
        }
      }
    },
    ...
  ]
}
```

## Supported Timeframes

- M1, M2, M3, M4, M5, M6, M10, M12, M15, M20, M30 (Minutes)
- H1, H2, H3, H4, H6, H8, H12 (Hours)
- D1 (Daily)
- W1 (Weekly)
- MN1 (Monthly)

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing required parameters)
- `500`: Internal Server Error (MetaTrader connection issues, etc.)

Error responses include an error message:
```json
{
  "error": "symbol parameter is required"
}
```

## Notes

- MetaTrader5 terminal must be running and logged in for the API to work
- The API uses the default MetaTrader5 installation path unless specified in `.env`
- Make sure you have the MetaTrader5 Python package installed (`pip install MetaTrader5`)

## License

MIT

