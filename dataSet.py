import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()
#  User Agent


# Login İnformation
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

LOGIN_URL = os.getenv('LOGIN_URL')


SIGNALS_URL = os.getenv('SIGNALS_URL')

# Telegram Bot API İnformation
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')   

TOP_100_ORDERED = [
    "BTC", "ETH", "USDT", "BNB", "USDC", "XRP", "ADA", "SOL", "DOT", "DOGE",
    "AVAX", "SHIB", "LTC", "LINK", "ALGO", "BCH", "XLM", "VET", "TRX", "FIL",
    "ETC", "MANA", "THETA", "ATOM", "ICP", "AAVE", "MKR", "XTZ", "CAKE", "EOS",
    "XMR", "NEO", "MIOTA", "KLAY", "HT", "COMP", "ZEC", "ENJ", "SUSHI", "CHZ",
    "HNT", "DCR", "FTM", "CRV", "SNX", "KSM", "HOT", "ONE", "AR", "GRT", "FLOW",
    "TFUEL", "AMP", "BAT", "CEL", "NEXO", "HBAR", "BIT", "STX", "OKB", "ZIL",
    "REN", "CELO", "1INCH", "BSV", "SC", "UMA", "OCEAN", "ANKR", "RVN", "XVG",
    "GLM", "QTUM", "LRC", "INJ", "AUDIO", "RSR", "EGLD", "DENT", "PAX", "LUNC",
    "SAFEMOON", "TWT", "POWR", "XEM", "KMD", "BNT", "OMG", "ANT", "ZRX", "BAL",
    "OXT", "NMR", "SRM", "STORJ", "GNO", "CVC", "FET", "WRX", "KAVA"
]

# pointer of static
TOP_100_DICT = {coin: idx + 1 for idx, coin in enumerate(TOP_100_ORDERED)}


#login function

def login_and_get_session():

    session = requests.Session()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    response = session.post(
        LOGIN_URL,
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        data = response.json()
        print("Login başarılı:", data.get("message"))
        token = data.get("token")
        if token:
            # We add Authorization header to the session for automatic use in subsequent requests
            session.headers.update({"Authorization": f"Bearer {token}"})
            return session
        else:
            print("Token alınamadı!")
            return None
    else:
        print("Giriş başarısız:", response.text)
        return None
# refresh the session
def refresh_session():
    print("Oturum süresi doldu , tekrar giriş yapılıyor...")
    return login_and_get_session()


#  signals response

def get_signals_api(session):
    resp = session.get(SIGNALS_URL)
    if resp.status_code == 401:
        print("Yetkilendirme hatası (401), oturum yenileniyor...")
        return None
    if resp.status_code == 200:
        try:
            data = resp.json()
            signals = data.get("signals", [])
            if len(signals) > 2:
                signals = signals[:2]
            return signals
        except Exception as e:
            print("JSON parse hatası:", e)
            return []
    else:
        print("Sinyaller alınamadı:", resp.status_code, resp.text)
        return []

#  add to telegram message

def send_telegram_message(message):
    """
    Belirtilen metni Telegram'a gönderir.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram mesajı gönderilemedi:", e)

def extract_base_coin(market):
    """
   If the market string is, for example, “BTCUSDT”, the base coin is output as “BTC”.
    If it has a different structure, make the corresponding edit
    """
    if market.endswith("USDT"):
        return market[:-4]  # "USDT" 4 characters
    return market


#  APP

def main():
    session = login_and_get_session()
    if not session:
        return
    
    start_message = "🚀🔥 **Özelleştirilmiş Bot Devrede!** 🔥🚀\n⚡ Hızlı & Güvenilir Sinyal Takibi Başladı!"
    send_telegram_message(start_message)

    seen_signals = set()

    while True:
        signals = get_signals_api(session)
        if signals is None:
            session = refresh_session()
            if not session:
                print("Yeniden giriş başarısız, çıkılıyor")
                break
            continue

        print(f"Sinyaller alındı: {len(signals)} adet.")

        if not signals:
            print("Yeni sinyal yok.")
        else:
            for s in signals:
                signal_id = s.get("_id")
                if not signal_id or signal_id in seen_signals:
                    continue

                market = s.get("market", "Bilinmiyor")
                base_coin = extract_base_coin(market).upper()
                # controllers top 100 in coinbase
                if base_coin not in TOP_100_DICT:
                    print(f"{base_coin} Top 100 listesinde yok, mesaj gönderilmiyor.")
                    seen_signals.add(signal_id)
                    continue

                rank = TOP_100_DICT[base_coin]
                if rank <= 20:
                    color_emoji = "🔴🔴🔴🔴🔴"  
                elif rank <= 50:
                    color_emoji = "🟠🟠🟠" 
                elif rank <= 100:
                    color_emoji = "🟡"  
                else:
                    seen_signals.add(signal_id)
                    continue

                side = s.get("signal_side", "Bilinmiyor").upper()
                time_str = s.get("time", "Bilinmiyor")
                price = s.get("signal_price", "Bilinmiyor")

                message = (
                    f"{color_emoji} <b>Yeni Sinyal!</b>\n"
                    f"Market: {market}\n"
                    f"Temel Coin: {base_coin} (Sıra: {rank})\n"
                    f"Yön: {side}\n"
                    f"Zaman: {time_str}\n"
                    f"Fiyat: {price}"
                )
                send_telegram_message(message)
                seen_signals.add(signal_id)

        time.sleep(1)

if __name__ == "__main__":
    main()
