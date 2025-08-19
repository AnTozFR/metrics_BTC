from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 277_275_004
    btc_held = 2395
    btc_yield_ytd = 55069

    btc_history = [
    {"date": "2025-08-12", "btc": 295.00, "price": 82399},
    {"date": "2025-08-08", "btc": 50.00, "price": 81472},
    {"date": "2025-07-30", "btc": 225.00, "price": 81346},
    {"date": "2025-07-25", "btc": 225.00, "price": 80466},
    {"date": "2025-07-16", "btc": 325.00, "price": 79534},
    {"date": "2025-07-11", "btc": 275.00, "price": 78516},
    {"date": "2025-07-07", "btc": 226.42, "price": 78228},
    {"date": "2025-07-01", "btc": 230.05, "price": 78022},
    {"date": "2025-06-24", "btc": 196.90, "price": 77988},
    {"date": "2025-06-19", "btc": 104.28, "price": 78480},
    {"date": "2025-06-13", "btc": 74.27,  "price": 78793},
    {"date": "2025-06-10", "btc": 45.32,  "price": 78060},
    {"date": "2025-06-05", "btc": 39.52,  "price": 78290},
    {"date": "2025-05-29", "btc": 24.53,  "price": 78567},
    {"date": "2025-05-23", "btc": 23.09,  "price": 77326},
    {"date": "2025-05-20", "btc": 16.42,  "price": 75512},
    {"date": "2025-05-14", "btc": 8.61,   "price": 73432},
    {"date": "2025-05-07", "btc": 4.85,   "price": 71766},
    {"date": "2025-04-30", "btc": 3.44,   "price": 72125},
    {"date": "2025-04-28", "btc": 2.30,   "price": 73913}
    ]

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        swc = yf.Ticker("3M8.F")
        swc_price = swc.info.get("currentPrice", 0)
        market_cap = swc.info.get("marketCap", 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * swc_price
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
        start_date = datetime.strptime("2025-04-28", "%Y-%m-%d")
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

        swc_hist = swc.history(period="2d")["Close"]
        swc_price_yesterday = swc_hist.iloc[-2] if len(swc_hist) >= 2 else None
        swc_price_change_pct = ((swc_price - swc_price_yesterday) / swc_price_yesterday * 100) if swc_price_yesterday else None

        # mNAV d’hier
        mn_nav_yesterday = (shares_fully_diluted * swc_price_yesterday) / (btc_price_yesterday * btc_held) if btc_price_yesterday and swc_price_yesterday else None
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
            "swc_price": round(swc_price, 2),
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
            "swc_price_change_pct": round(swc_price_change_pct, 2) if swc_price_change_pct else None,
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

def get_swc_metrics():
    return get_metrics()
