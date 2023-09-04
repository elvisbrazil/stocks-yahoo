from flask import Flask, jsonify, render_template
from flask_caching import Cache
import yfinance as yf
from datetime import datetime, timedelta
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

# Configuração do Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Use um cache simples em memória para fins de demonstração

@app.route('/api/<symbol>')
@cache.cached(timeout=600)  # Cache válido por 10 minutos (ajuste conforme necessário)
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
            'profile': translator.translate(info.get('longBusinessSummary', ''), src='en', dest='pt').text
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


@app.route('/')
@cache.cached(timeout=600) 
def index():
    # Obtém os principais índices do mundo
    indices_mundo = {
        'Dow Jones': '^DJI',
        'S&P 500': '^GSPC',
        'NASDAQ': '^IXIC',
        'FTSE 100': '^FTSE',
        'Nikkei 225': '^N225'
    }

    # Obtém informações sobre 10 ações brasileiras (incluindo o último preço em tempo real)
    acoes_brasileiras = [
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
        'WEGE3.SA', 'BBAS3.SA', 'MGLU3.SA', 'SUZB3.SA', '^BVSP', 'USDBRL=X'
    ]

    stock_data = []

    for symbol in acoes_brasileiras:
        stock = yf.Ticker(symbol)
        info = stock.info
        last_trade = stock.history(period="1d")
        if not last_trade.empty:
            last_price = last_trade['Close'][0]
        else:
            last_price = None
        stock_data.append({
            'symbol': info.get('symbol', symbol),
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'country': info.get('country', ''),
            'last_price': last_price
        })

    return render_template('index.html', indices_mundo=indices_mundo, acoes_brasileiras=stock_data)


if __name__ == '__main__':
    app.run(debug=True)
