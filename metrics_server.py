from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/api/metrics')
def get_metrics():
    # Données fixes
    shares_fully_diluted = 304_953_371
    btc_held = 1471
    btc_yield_ytd = 1097.6  # soit +1097% sur l'année

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        altbg = yf.Ticker("ALTBG.PA")
        altbg_price = altbg.info.get("currentPrice", 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * altbg_price
        mn_nav = market_cap_fully_diluted / btc_nav if btc_nav else None

        # Début du programme
        start_date = datetime.strptime("2024-12-11", "%Y-%m-%d")
        days_since_start = (datetime.today() - start_date).days

        # Vitesse d'accumulation linéaire
        btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

        # Yield linéaire basé sur BTC YTD (en % converti en multiplicatif)
        yield_daily_pct = (btc_yield_ytd / days_since_start) / 100 if days_since_start > 0 else None
        yield_monthly_pct = yield_daily_pct * 30 if yield_daily_pct else None

        # Temps nécessaire pour atteindre mNAV avec ce rythme
        months_to_cover_mnav_yield_linear = mn_nav / yield_monthly_pct if mn_nav and yield_monthly_pct else None
        days_to_cover_mnav_yield_linear = months_to_cover_mnav_yield_linear * 30 if months_to_cover_mnav_yield_linear else None

        return jsonify({
            "btc_price": round(btc_price, 2),
            "btc_held": btc_held,
            "btc_nav": round(btc_nav, 2),
            "altbg_price": round(altbg_price, 2),
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
            "diluted_share": shares_fully_diluted,
            "mn_nav": round(mn_nav, 3) if mn_nav else None,
            "btc_yield_ytd": btc_yield_ytd,
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,
            "yield_daily_pct": round(yield_daily_pct * 100, 3) if yield_daily_pct else None,  # En %
            "yield_monthly_pct": round(yield_monthly_pct * 100, 1) if yield_monthly_pct else None,  # En %
            "months_to_cover_mnav_yield_linear": round(months_to_cover_mnav_yield_linear, 2) if months_to_cover_mnav_yield_linear else None,
            "days_to_cover_mnav_yield_linear": round(days_to_cover_mnav_yield_linear, 1) if days_to_cover_mnav_yield_linear else None
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
