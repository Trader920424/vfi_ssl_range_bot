
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime

api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

symbol = 'BTC/USDT'
timeframe = '1m'
leverage = 5
order_size_pct = 0.05

def calculate_indicators(df):
    df['vfi'] = df['volume'] * (df['close'] - df['open']) / df['open']
    df['vfi'] = df['vfi'].rolling(window=14).mean()

    df['ssl_up'] = df['close'].rolling(window=10).mean()
    df['ssl_down'] = df['close'].rolling(window=10).min()

    df['range'] = df['high'] - df['low']
    df['range_filter'] = df['range'].rolling(window=10).mean()
    return df

def get_position():
    positions = exchange.fapiPrivateGetPositionRisk()
    for p in positions:
        if p['symbol'] == symbol.replace('/', ''):
            return float(p['positionAmt'])
    return 0

def place_order(side, amount):
    try:
        exchange.set_leverage(leverage, symbol)
        order = exchange.create_market_order(symbol, side, amount)
        print(f"[{datetime.now()}] {side.upper()} 주문 체결: 수량={amount}")
    except Exception as e:
        print(f"[{datetime.now()}] 주문 실패: {e}")

def run_bot():
    print(f"[{datetime.now()}] 자동매매 시작...")
    balance = exchange.fetch_balance()
    usdt_balance = balance['total']['USDT']
    amount = (usdt_balance * order_size_pct * leverage) / exchange.fetch_ticker(symbol)['last']

    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = calculate_indicators(df)

            current = df.iloc[-1]
            previous = df.iloc[-2]
            position = get_position()

            if current['vfi'] > 0 and current['close'] > current['ssl_up'] and current['range'] > current['range_filter']:
                if position <= 0:
                    place_order('buy', amount)

            elif current['vfi'] < 0 and current['close'] < current['ssl_down'] and current['range'] > current['range_filter']:
                if position >= 0:
                    place_order('sell', amount)

            time.sleep(60)

        except Exception as e:
            print(f"[{datetime.now()}] 오류 발생: {e}")
            time.sleep(30)

if __name__ == '__main__':
    run_bot()
