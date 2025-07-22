from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 320_990_295
    btc_held = 1933
    btc_yield_ytd = 1368.3

    btc_history = [
    {"date": "2024-11-05", "btc": 15, "price": 63729},
    {"date": "2024-12-04", "btc": 25, "price": 90511},
    {"date": "2025-03-26", "btc": 580, "price": 81550},
    {"date": "2025-05-22", "btc": 227, "price": 93518},
    {"date": "2025-06-02", "btc": 624, "price": 96447},
    {"date": "2025-06-18", "btc": 182, "price": 93264},
    {"date": "2025-06-23", "btc": 75, "price": 91792},
    {"date": "2025-06-30", "btc": 60, "price": 91879},
    {"date": "2025-07-07", "btc": 116, "price": 92175},
    {"date": "2025-07-14", "btc": 29, "price": 95225}
    ]

    fundraising_data = [
        {"date": "2024-11-05", "type": "Capital increase", "detail": "BTC strategy launch (0.20€/share)", "montant": 1},
        {"date": "2024-12-04", "type": "Capital increase", "detail": "Subscription at 0.30€/share", "montant": 2.5},
        {"date": "2025-03-06", "type": "OCA Tranche 2", "detail": "Fulgur Ventures, Adam Back, UTXO, TOBAM, Ludovic C.-Laurans (0.544€/share)", "montant": 48.6},
        {"date": "2025-04-07", "type": "BSA 2025-01", "detail": "Free allocation to shareholders (exercise possible at 0.544€)", "montant": 7.3},
        {"date": "2025-05-09", "type": "Capital increase", "detail": "Subscription at 1.0932€/share", "montant": 9.9},
        {"date": "2025-05-12", "type": "OCA Tranche 2", "detail": "Adam Back (0.707€/share, 30% premium)", "montant": 12.1},
        {"date": "2025-05-20", "type": "OCA", "detail": "Private placement + reserved capital increase (1.28€/share)", "montant": 8.6},
        {"date": "2025-05-26", "type": "OCA Tranche 2 + conversion", "detail": "Fulgur Ventures, UTXO Management, Moonlight Capital, Adam Back", "montant": 63.3},
        {"date": "2025-06-12", "type": "OCA mixed + conversions", "detail": "TOBAM, Ludovic Chechin Laurans and Adam Back", "montant": 9.7},
        {"date": "2025-06-17", "type": "ATM Type", "detail": "TOBAM (4.49€/share) - ATM Type #1", "montant": 7.2},
        {"date": "2025-06-24", "type": "ATM Type", "detail": "TOBAM (5.085€/share) - ATM Type #2", "montant": 4.1},
        {"date": "2025-07-01", "type": "ATM Type", "detail": "TOBAM (5.251€/share) - ATM Type #3", "montant": 1},
        {"date": "2025-07-01", "type": "OCA A-04 and B-04 Tranche 1", "detail": "Reserved issuance TOBAM and Adam Back (5.174€/share)", "montant": 10},
        {"date": "2025-07-08", "type": "ATM Type", "detail": "TOBAM (4.056€/share) - ATM Type #4", "montant": 3},
        {"date": "2025-07-15", "type": "ATM Type", "detail": "TOBAM (3.95€/share) - ATM Type #5", "montant": 1.1},
        {"date": "2025-07-15", "type": "Reserved capital increase", "detail": "Adam Back (4.01€/share)", "montant": 5},
    ]

    capital_data = {
        "labels": [
            "Fulgur Ventures",
            "Public & Institutional",
            "Adam Back",
            "Executives",
            "TOBAM",
            "UTXO Management",
            "Free Shares"
        ],
        "values": [
            145_911_009,
            100_975_068,
            35_163_699,
            18_418_953,
            10_642_356,
            7_999_210,
            1_880_000
        ]
    }

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        altbg = yf.Ticker("ALTBG.PA")
        altbg_price = altbg.info.get("currentPrice", 0)
        market_cap = altbg.info.get("marketCap", 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * altbg_price
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
        start_date = datetime.strptime("2024-11-05", "%Y-%m-%d")
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

        altbg_hist = altbg.history(period="2d")["Close"]
        altbg_price_yesterday = altbg_hist.iloc[-2] if len(altbg_hist) >= 2 else None
        altbg_price_change_pct = ((altbg_price - altbg_price_yesterday) / altbg_price_yesterday * 100) if altbg_price_yesterday else None

        # mNAV d’hier
        mn_nav_yesterday = (shares_fully_diluted * altbg_price_yesterday) / (btc_price_yesterday * btc_held) if btc_price_yesterday and altbg_price_yesterday else None
        mn_nav_change_pct = ((mn_nav - mn_nav_yesterday) / mn_nav_yesterday * 100) if mn_nav and mn_nav_yesterday else None

        # PCV d’hier + variation
        pcv = (mn_nav - 1) / months_to_cover if months_to_cover else None
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
            "altbg_price": round(altbg_price, 2),
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
            "altbg_price_change_pct": round(altbg_price_change_pct, 2) if altbg_price_change_pct else None,
            "mn_nav_change_pct": round(mn_nav_change_pct, 2) if mn_nav_change_pct else None,
            "shares_fully_diluted": shares_fully_diluted,
            "btc_history": btc_history,
            "fundraising_data": fundraising_data,
            "capital_data": capital_data,
            "btc_per_share": btc_per_share,
            "satoshi_per_share": satoshi_per_share,
            "btc_value_per_share_eur": btc_value_per_share_eur,
            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2),
            "btc_torque": btc_torque,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_altbg_metrics():
    return get_metrics()
