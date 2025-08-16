from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 865_942_925
    btc_held = 18113
    btc_yield_ytd = 460.2

    btc_history = [
    {"date": "2024-04-23", "btc": 97.85, "price": 66018},
    {"date": "2024-05-09", "btc": 19.87, "price": 64626},
    {"date": "2024-06-10", "btc": 23.35, "price": 68136},
    {"date": "2024-07-01", "btc": 20.20, "price": 61512},
    {"date": "2024-07-08", "btc": 42.47, "price": 58578},
    {"date": "2024-07-16", "btc": 21.88, "price": 57751},
    {"date": "2024-07-22", "btc": 20.38, "price": 71882},
    {"date": "2024-08-13", "btc": 57.10, "price": 59647},
    {"date": "2024-08-20", "btc": 57.27, "price": 60104},
    {"date": "2024-09-10", "btc": 38.46, "price": 54772},
    {"date": "2024-10-01", "btc": 107.91, "price": 64576},
    {"date": "2024-10-03", "btc": 23.97, "price": 60926},
    {"date": "2024-10-07", "btc": 108.79, "price": 62027},
    {"date": "2024-10-11", "btc": 109.00, "price": 61540},
    {"date": "2024-10-15", "btc": 106.98, "price": 62738},
    {"date": "2024-10-16", "btc": 5.91, "price": 65508},
    {"date": "2024-10-28", "btc": 156.78, "price": 66613},
    {"date": "2024-11-19", "btc": 124.12, "price": 91171},
    {"date": "2024-12-23", "btc": 619.70, "price": 97644},
    {"date": "2025-02-17", "btc": 269.43, "price": 98060},
    {"date": "2025-02-20", "btc": 68.59, "price": 97108},
    {"date": "2025-02-25", "btc": 135.00, "price": 96379},
    {"date": "2025-03-03", "btc": 156.00, "price": 86636},
    {"date": "2025-03-05", "btc": 497.00, "price": 89398},
    {"date": "2025-03-12", "btc": 162.00, "price": 83628},
    {"date": "2025-03-18", "btc": 150.00, "price": 83956},
    {"date": "2025-03-24", "btc": 150.00, "price": 83412},
    {"date": "2025-03-31", "btc": 696.00, "price": 97502},
    {"date": "2025-04-02", "btc": 160.00, "price": 83711},
    {"date": "2025-04-14", "btc": 319.00, "price": 82549},
    {"date": "2025-04-21", "btc": 330.00, "price": 85605},
    {"date": "2025-04-24", "btc": 145.00, "price": 93623},
    {"date": "2025-05-07", "btc": 555.00, "price": 96134},
    {"date": "2025-05-12", "btc": 1241.00, "price": 102119},
    {"date": "2025-05-19", "btc": 1004.00, "price": 103873},
    {"date": "2025-06-02", "btc": 1088.00, "price": 107771},
    {"date": "2025-06-16", "btc": 1112.00, "price": 105435},
    {"date": "2025-06-23", "btc": 1111.00, "price": 106408},
    {"date": "2025-06-26", "btc": 1234.00, "price": 107557},
    {"date": "2025-06-30", "btc": 1005.00, "price": 107601},
    {"date": "2025-07-07", "btc": 2205.00, "price": 108237},
    {"date": "2025-07-14", "btc": 797.00, "price": 117451},
    {"date": "2025-07-28", "btc": 780.00, "price": 118622},
    {"date": "2025-08-04", "btc": 463.00, "price": 115895},
    {"date": "2025-08-12", "btc": 518.00, "price": 118519}
    ]

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        mtplf = yf.Ticker("DN3.F")
        mtplf_price = mtplf.info.get("currentPrice", 0)

        mtplf_japan = yf.Ticker("3350.T")
        market_cap_jpy = mtplf_japan.info.get("marketCap", 0)
        
        # Taux de change EUR/JPY
        eur_jpy = yf.Ticker("EURJPY=X")
        eur_jpy_rate = eur_jpy.history(period="1d")["Close"].iloc[-1]
        
        # Market cap convertie en euros
        market_cap = market_cap_jpy / eur_jpy_rate if market_cap_jpy and eur_jpy_rate else None

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
        start_date = datetime.strptime("2020-08-10", "%Y-%m-%d")
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
        pcv_yesterday = (mn_nav_yesterday - 1) / months_to_cover if mn_nav_yesterday and months_to_cover else None
        pcv_change_pct = ((pcv - pcv_yesterday) / pcv_yesterday * 100) if pcv and pcv_yesterday else None

        btc_per_share = btc_held / shares_fully_diluted if shares_fully_diluted else None

        satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None

        btc_value_per_share_eur = btc_per_share * btc_price if btc_per_share is not None else None

        invest_price = sum(entry["btc"] * entry["price"] for entry in btc_history)

        btc_gain = btc_nav - invest_price

        btc_torque = btc_nav / invest_price

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
            "shares_fully_diluted": shares_fully_diluted,
            "btc_history": btc_history,
            "btc_per_share": btc_per_share,
            "satoshi_per_share": satoshi_per_share,
            "btc_value_per_share_eur": btc_value_per_share_eur,
            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2),
            "btc_torque": btc_torque,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_mtplf_metrics():
    return get_metrics()

