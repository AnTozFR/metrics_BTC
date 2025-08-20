from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 352_95_000
    btc_held = 911.29
    btc_yield_ytd = 6013

    btc_history = [
    {"date": "2025-05-22", "btc": 4.39, "price": 110913},
    {"date": "2025-05-30", "btc": 1.85, "price": 105178},
    {"date": "2025-06-05", "btc": 7.70, "price": 105365},
    {"date": "2025-06-12", "btc": 10.46, "price": 109273},
    {"date": "2025-06-16", "btc": 144.80, "price": 108636},
    {"date": "2025-06-25", "btc": 31.01, "price": 107800},
    {"date": "2025-07-02", "btc": 47.33, "price": 107798},
    {"date": "2025-07-09", "btc": 46.93, "price": 108973},
    {"date": "2025-07-16", "btc": 75.53, "price": 116656},
    {"date": "2025-07-21", "btc": 140.25, "price": 118918},
    {"date": "2025-07-23", "btc": 117.93, "price": 117707},
    {"date": "2025-07-30", "btc": 56.90, "price": 117620},
    {"date": "2025-08-01", "btc": 17.47, "price": 116965},
    {"date": "2025-08-06", "btc": 60.60, "price": 115190},
    {"date": "2025-08-13", "btc": 45.80, "price": 119085},
    {"date": "2025-08-20", "btc": 102.19, "price": 120538}
    ]

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        h100 = yf.Ticker("GS9.F")
        h100_price = h100.info.get("currentPrice", 0)
        market_cap = h100.info.get("marketCap", 0)
        if market_cap is None:
            market_cap = float("nan")

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * h100_price
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

        h100_hist = h100.history(period="2d")["Close"]
        h100_price_yesterday = h100_hist.iloc[-2] if len(h100_hist) >= 2 else None
        h100_price_change_pct = ((h100_price - h100_price_yesterday) / h100_price_yesterday * 100) if h100_price_yesterday else None

        # mNAV d’hier
        mn_nav_yesterday = (shares_fully_diluted * h100_price_yesterday) / (btc_price_yesterday * btc_held) if btc_price_yesterday and h100_price_yesterday else None
        mn_nav_change_pct = ((mn_nav - mn_nav_yesterday) / mn_nav_yesterday * 100) if mn_nav and mn_nav_yesterday else None

        # PCV d’hier + variation
        pcv_yesterday = (mn_nav_yesterday - 1) / months_to_cover if mn_nav_yesterday and months_to_cover else None
        pcv_change_pct = ((pcv - pcv_yesterday) / pcv_yesterday * 100) if pcv and pcv_yesterday else None

        btc_per_share = btc_held / shares_fully_diluted if shares_fully_diluted else None

        satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None

        btc_value_per_share_eur = btc_per_share * btc_price if btc_per_share is not None else None

        # --- Conversion USD -> EUR ---
        eur_usd = yf.Ticker("EURUSD=X").history(period="1d")["Close"].iloc[-1]
        usd_to_eur = 1 / eur_usd if eur_usd else None

        # Montant total investi en USD
        invest_price_usd = sum(entry["btc"] * entry["price"] for entry in btc_history)
        invest_price = invest_price_usd * usd_to_eur if usd_to_eur else None

        btc_gain = btc_nav - invest_price

        btc_torque = btc_nav / invest_price

        return jsonify({
            "btc_held": btc_held,
            "btc_yield_ytd": btc_yield_ytd,
            "btc_price": round(btc_price, 2),
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,
            "h100_price": round(h100_price, 2),
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
            "h100_price_change_pct": round(h100_price_change_pct, 2) if h100_price_change_pct else None,
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

def get_h100_metrics():
    return get_metrics()
