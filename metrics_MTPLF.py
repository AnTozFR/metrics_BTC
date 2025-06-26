from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

app = Flask(__name__)
CORS(app)

@app.route('/api/metrics')
def get_metrics():
    # Données fixes
    shares_fully_diluted = 759_067_925
    btc_held = 12345
    btc_yield_ytd = 315.01

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        mtplf = yf.Ticker("DN3.F")
        mtplf_price = mtplf.info.get("currentPrice", 0)
        market_cap = mtplf.info.get("marketCap", 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * mtplf_price
        mn_nav = market_cap_fully_diluted / btc_nav if btc_nav else None

        # Étapes pour retrouver les 5.43 months :
        start_of_year = datetime(datetime.today().year, 1, 1)
        days_elapsed = (datetime.today() - start_of_year).days
        ytd_growth_factor = 1 + btc_yield_ytd / 100
        daily_yield = ytd_growth_factor ** (1 / days_elapsed) - 1

        ln_mnav = math.log(mn_nav)
        ln_yield = math.log(1 + daily_yield)
        days_to_cover = ln_mnav / ln_yield if ln_yield != 0 else None
        months_to_cover = days_to_cover / 30 if days_to_cover else None

        # Début du programme
        start_date = datetime.strptime("2024-04-08", "%Y-%m-%d")
        days_since_start = (datetime.today() - start_date).days

        # Vitesse d'accumulation linéaire
        btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

        # Nombre de mois entiers écoulés depuis le début de l'année
        today = datetime.today()
        months_elapsed = today.month - 1 + (1 if today.day >= 1 else 0)  # +1 si on veut inclure le mois en cours
        btc_yield_monthly = btc_yield_ytd / months_elapsed if months_elapsed > 0 else None

        # PCV
        pcv = (mn_nav - 1) / months_to_cover if months_to_cover else None

        # Historique sur 2 jours (doit venir avant tout calcul basé dessus)
        btc_hist = btc.history(period="2d")["Close"]
        btc_price_yesterday = btc_hist.iloc[-2] if len(btc_hist) >= 2 else None
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None

        mtplf_hist = mtplf.history(period="2d")["Close"]
        mtplf_price_yesterday = mtplf_hist.iloc[-2] if len(mtplf_hist) >= 2 else None
        mtplf_price_change_pct = ((mtplf_price - mtplf_price_yesterday) / mtplf_price_yesterday * 100) if mtplf_price_yesterday else None

        # mNAV d’hier
        mn_nav_yesterday = (shares_fully_diluted * mtplf_price_yesterday) / (btc_price_yesterday * btc_held) if btc_price_yesterday and mtplf_price_yesterday else None
        mn_nav_change_pct = ((mn_nav - mn_nav_yesterday) / mn_nav_yesterday * 100) if mn_nav and mn_nav_yesterday else None

        # PCV d’hier + variation
        pcv = (mn_nav - 1) / months_to_cover if months_to_cover else None
        pcv_yesterday = (mn_nav_yesterday - 1) / months_to_cover if mn_nav_yesterday and months_to_cover else None
        pcv_change_pct = ((pcv - pcv_yesterday) / pcv_yesterday * 100) if pcv and pcv_yesterday else None


        return jsonify({
            "btc_held": btc_held,
            "btc_yield_ytd": btc_yield_ytd,
            "btc_price": round(btc_price, 2),
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,
            "mtplf_price": round(mtplf_price, 2),
            "btc_nav": round(btc_nav, 2),
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
            "market_cap": round(market_cap, 2),
            "mn_nav": round(mn_nav, 3) if mn_nav else None,
            "daily_yield_pct": round(daily_yield * 100, 3),
            "days_to_cover": round(days_to_cover, 2) if days_to_cover else None,
            "pcv": round(pcv, 3) if pcv else None,
            "pcv_change_pct": round(pcv_change_pct, 2) if pcv_change_pct else None,
            "btc_yield_monthly_pct": round(btc_yield_monthly, 2) if btc_yield_monthly else None,
            "months_to_cover": round(months_to_cover, 2) if months_to_cover else None,
            "btc_price_change_pct": round(btc_price_change_pct, 2) if btc_price_change_pct else None,
            "mtplf_price_change_pct": round(mtplf_price_change_pct, 2) if mtplf_price_change_pct else None,
            "mn_nav_change_pct": round(mn_nav_change_pct, 2) if mn_nav_change_pct else None,
            "shares_fully_diluted": shares_fully_diluted
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_mtplf_metrics():
    with app.test_request_context():
        return get_metrics()

if __name__ == '__main__':
    app.run(debug=True)
