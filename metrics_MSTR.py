from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 316_710_000
    btc_held = 628946
    btc_yield_ytd = 25

    btc_history = [
    {"date": "2020-08-10", "btc": 21454, "price": 11652},
    {"date": "2020-09-14", "btc": 16796, "price": 10419},
    {"date": "2020-12-04", "btc": 2574,  "price": 19427},
    {"date": "2020-12-21", "btc": 29646, "price": 21925},
    {"date": "2021-01-22", "btc": 314,   "price": 31808},
    {"date": "2021-02-02", "btc": 295,   "price": 33110},
    {"date": "2021-02-19", "btc": 19452, "price": 52765},
    {"date": "2021-03-01", "btc": 328,   "price": 45710},
    {"date": "2021-03-05", "btc": 205,   "price": 48888},
    {"date": "2021-03-12", "btc": 262,   "price": 57146},
    {"date": "2021-04-05", "btc": 253,   "price": 59339},
    {"date": "2021-05-13", "btc": 271,   "price": 55339},
    {"date": "2021-05-18", "btc": 229,   "price": 43663},
    {"date": "2021-06-21", "btc": 13005, "price": 37617},
    {"date": "2021-08-24", "btc": 3907,  "price": 45294},
    {"date": "2021-09-13", "btc": 5050,  "price": 48099},
    {"date": "2021-11-29", "btc": 7002,  "price": 59187},
    {"date": "2021-12-09", "btc": 1434,  "price": 57477},
    {"date": "2021-12-30", "btc": 1914,  "price": 49429},
    {"date": "2022-02-01", "btc": 660,   "price": 37814},
    {"date": "2022-04-05", "btc": 4167,  "price": 42194},
    {"date": "2022-06-29", "btc": 480,   "price": 20817},
    {"date": "2022-09-20", "btc": 301,   "price": 19851},
    {"date": "2022-12-28", "btc": 2501,  "price": 17847},
    {"date": "2023-03-23", "btc": 6455,  "price": 23238},
    {"date": "2023-04-05", "btc": 1045,  "price": 28016},
    {"date": "2023-06-28", "btc": 12333, "price": 28136},
    {"date": "2023-08-01", "btc": 467,   "price": 30788},
    {"date": "2023-09-25", "btc": 5445,  "price": 27053},
    {"date": "2023-11-30", "btc": 155,   "price": 34495},
    {"date": "2023-12-13", "btc": 16130, "price": 36785},
    {"date": "2023-12-27", "btc": 14620, "price": 42110},
    {"date": "2024-02-06", "btc": 850,   "price": 43723},
    {"date": "2024-02-26", "btc": 3000,  "price": 51813},
    {"date": "2024-03-11", "btc": 12000, "price": 68477},
    {"date": "2024-03-19", "btc": 9245,  "price": 67382},
    {"date": "2024-04-29", "btc": 155,   "price": 63397},
    {"date": "2024-06-20", "btc": 11931, "price": 65883},
    {"date": "2024-08-01", "btc": 169,   "price": 67455},
    {"date": "2024-09-13", "btc": 18300, "price": 60408},
    {"date": "2024-09-20", "btc": 7420,  "price": 61750},
    {"date": "2024-11-11", "btc": 27200, "price": 74463},
    {"date": "2024-11-18", "btc": 51780, "price": 88627},
    {"date": "2024-11-25", "btc": 55500, "price": 97862},
    {"date": "2024-12-02", "btc": 15400, "price": 97403},
    {"date": "2024-12-09", "btc": 21550, "price": 98783},
    {"date": "2024-12-16", "btc": 15350, "price": 100386},
    {"date": "2024-12-23", "btc": 5262,  "price": 106662},
    {"date": "2024-12-30", "btc": 2138,  "price": 97837},
    {"date": "2025-01-06", "btc": 1070,  "price": 94004},
    {"date": "2025-01-13", "btc": 2530,  "price": 95972},
    {"date": "2025-01-21", "btc": 11000, "price": 101191},
    {"date": "2025-01-27", "btc": 10107, "price": 105596},
    {"date": "2025-02-10", "btc": 7633,  "price": 97255},
    {"date": "2025-02-24", "btc": 20356, "price": 97514},
    {"date": "2025-03-17", "btc": 130,   "price": 82981},
    {"date": "2025-03-24", "btc": 6911,  "price": 84529},
    {"date": "2025-03-31", "btc": 22048, "price": 86969},
    {"date": "2025-04-14", "btc": 3459,  "price": 82618},
    {"date": "2025-04-21", "btc": 6556,  "price": 84785},
    {"date": "2025-04-28", "btc": 15355, "price": 92737},
    {"date": "2025-05-05", "btc": 1895,  "price": 95167},
    {"date": "2025-05-12", "btc": 13390, "price": 99856},
    {"date": "2025-05-19", "btc": 7390,  "price": 103498},
    {"date": "2025-05-26", "btc": 4020,  "price": 106237},
    {"date": "2025-06-02", "btc": 705,   "price": 106495},
    {"date": "2025-06-09", "btc": 1045,  "price": 105426},
    {"date": "2025-06-16", "btc": 10100, "price": 104080},
    {"date": "2025-06-23", "btc": 245,   "price": 105856},
    {"date": "2025-06-30", "btc": 4980,  "price": 106801},
    {"date": "2025-07-14", "btc": 4225,  "price": 111827},
    {"date": "2025-07-21", "btc": 6220,  "price": 118940},
    {"date": "2025-07-29", "btc": 21021, "price": 117256},
    {"date": "2025-08-11", "btc": 155,   "price": 116401},
    ]

    try:
        # Données live
        btc = yf.Ticker("BTC-USD")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        mstr = yf.Ticker("MSTR")
        mstr_price = mstr.info.get("currentPrice", 0)
        market_cap = mstr.info.get("marketCap", 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * mstr_price
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

        mstr_hist = mstr.history(period="2d")["Close"]
        mstr_price_yesterday = mstr_hist.iloc[-2] if len(mstr_hist) >= 2 else None
        mstr_price_change_pct = ((mstr_price - mstr_price_yesterday) / mstr_price_yesterday * 100) if mstr_price_yesterday else None

        # mNAV d’hier
        mn_nav_yesterday = (shares_fully_diluted * mstr_price_yesterday) / (btc_price_yesterday * btc_held) if btc_price_yesterday and mstr_price_yesterday else None
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
            "mstr_price": round(mstr_price, 2),
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
            "mstr_price_change_pct": round(mstr_price_change_pct, 2) if mstr_price_change_pct else None,
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

def get_mstr_metrics():
    return get_metrics()

