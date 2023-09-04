from flask import Flask, jsonify, render_template, request
from flask_caching import Cache
import yfinance as yf
from datetime import datetime, timedelta
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

# Configuração do Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Use um cache simples em memória para fins de demonstração

# Importe a lista de ações brasileiras do arquivo brazilian_stocks.py
from brazilian_stocks import brazilian_stocks

# Função para ajustar o símbolo com ".SA" para ações brasileiras
def adjust_symbol(symbol):
    if symbol in brazilian_stocks:
        return f'{symbol}.SA'
    return symbol

@app.route('/api/<symbol>')
@cache.cached(timeout=600)  # Cache válido por 10 minutos (ajuste conforme necessário)
def get_stock_info(symbol):
    try:
        # Ajuste o símbolo
        adjusted_symbol = adjust_symbol(symbol)

        stock = yf.Ticker(adjusted_symbol)
        info = stock.info
        summary = {
            'symbol': info.get('symbol', adjusted_symbol),
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'country': info.get('country', ''),
            'previous_close': info.get('regularMarketPreviousClose', None),
            'profile': translator.translate(info.get('longBusinessSummary', ''), src='en', dest='pt').text
        }

        # Resto do código...

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

    stock_data = []

    for symbol in brazilian_stocks:
        try:
            # Ajuste o símbolo
            adjusted_symbol = adjust_symbol(symbol)

            stock = yf.Ticker(adjusted_symbol)
            info = stock.info
            last_trade = stock.history(period="1d")
            if not last_trade.empty:
                last_price = last_trade['Close'][0]
            else:
                last_price = None
            stock_data.append({
                'symbol': info.get('symbol', adjusted_symbol),
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'country': info.get('country', ''),
                'last_price': last_price
            })
        except Exception as e:
            # Se houver um erro ao buscar os dados, adicione um dicionário vazio
            stock_data.append({'symbol': symbol, 'error': str(e)})

    return render_template('index.html', indices_mundo=indices_mundo, acoes_brasileiras=stock_data)

if __name__ == '__main__':
    app.run(debug=True)
