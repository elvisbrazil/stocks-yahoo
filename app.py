from flask import Flask, jsonify
import yfinance as yf
from datetime import datetime, timedelta
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

@app.route('/api/<symbol>') ### Escolha aqui sua rota
def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        summary = {
            'symbol': info.get('symbol', symbol),
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'country': info.get('country', ''),
            'previous_close': info.get('regularMarketPreviousClose', None),
            'profile': translator.translate(info.get('longBusinessSummary', ''), src='en', dest='pt').text  #tradução ocorre aqui 
        }
        
        end_time = datetime.now()
        start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        data = stock.history(start=start_time, end=end_time, interval="5m")
        if not data.empty:
            quotes = []
            for idx, row in data.iterrows():
                quote = {
                    'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                }
                quotes.append(quote)
            summary['quotes'] = quotes
        
        last_price = info.get('regularMarketPrice', None)
        summary['last_price'] = last_price
        
        last_refresh = datetime.fromtimestamp(info.get('regularMarketTime', 0)).strftime('%Y-%m-%d %H:%M:%S')
        summary['last_refresh'] = last_refresh
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
