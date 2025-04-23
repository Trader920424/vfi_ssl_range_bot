
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime
import requests

# 텔레그램 설정
TELEGRAM_TOKEN = '7596695404:AAHxNcoEAULIZwOLf0e_WjuNiZxW5OQozcI'
TELEGRAM_CHAT_ID = '5411352603'

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[텔레그램 전송 실패] {e}")

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

send_telegram("[비밀병기] 자동매매 봇 시작됨.")

try:
    exchange.fapiPrivate_post_leverage({'symbol': symbol.replace('/', ''), 'leverage': leverage})
except Exception as e:
    send_telegram(f"[레버리지 설정 실패] {e}")
    exit()

while True:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # === 비밀병기 지표 조합 계산 ===
        df['vfi'] = df['volume']  # 예시: 실제는 VFI 계산 필요
        df['ssl'] = np.where(df['close'] > df['close'].rolling(10).mean(), 1, -1)
        df['range'] = df['high'] - df['low']

        signal = ''
        if df['vfi'].iloc[-1] > df['vfi'].mean() and df['ssl'].iloc[-1] == 1:
            signal = 'buy'
        elif df['vfi'].iloc[-1] < df['vfi'].mean() and df['ssl'].iloc[-1] == -1:
            signal = 'sell'

        balance = exchange.fetch_balance({"type": "future"})
        usdt = balance['total']['USDT']
        price = df['close'].iloc[-1]
        amount = round((usdt * 0.95 * leverage) / price, 3)

        if signal == 'buy':
            order = exchange.create_market_buy_order(symbol, amount)
            send_telegram(f"[롱 진입] 수량: {amount}, 가격: {price}")
        elif signal == 'sell':
            order = exchange.create_market_sell_order(symbol, amount)
            send_telegram(f"[숏 진입] 수량: {amount}, 가격: {price}")

        time.sleep(60)

    except Exception as e:
        send_telegram(f"[에러 발생] {e}")
        time.sleep(10)
