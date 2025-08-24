from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
from datetime import timedelta
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 277_275_004
    btc_held = 2395
    btc_yield_ytd = 55069
    q2_yield = 23112

    rows = [
        # date, acquired, avg_cost_after (GBP/BTC)
        ("2025-04-28", 2.30, 73913, 2.30),
        ("2025-04-30", 3.44, 72125, 5.74),
        ("2025-05-07", 4.85, 71766, 10.59),
        ("2025-05-14", 8.61, 73432, 19.20),
        ("2025-05-20",16.42, 75512, 35.62),
        ("2025-05-23",23.09, 77326, 58.71),
        ("2025-05-29",24.53, 78567, 83.24),
        ("2025-06-05",39.52, 78290,122.76),
        ("2025-06-10",45.32, 78060,168.08),
        ("2025-06-13",74.27, 78793,242.34),
        ("2025-06-19",104.28,78480,346.63),
        ("2025-06-24",196.90,77988,543.52),
        ("2025-07-01",230.05,78022,773.58),
        ("2025-07-07",226.42,78228,1000.00),
        ("2025-07-11",275.00,78516,1275.00),
        ("2025-07-16",325.00,79534,1600.00),
        ("2025-07-25",225.00,80466,1825.00),
        ("2025-07-30",225.00,81346,2050.00),
        ("2025-08-08",50.00,  81472,2100.00),
        ("2025-08-12",295.00,82399,2395.00),
        ]
    
    prev_total = 0
    btc_history = []
    for d, acq, avg, hold in rows:
        cum_total = avg * hold
        trade_cost = cum_total - prev_total
        unit_price = trade_cost / acq
        btc_history.append({"date": d, "btc": round(acq, 2), "price": round(unit_price)})
        prev_total = cum_total


    try:
        # Données live
        btc = yf.Ticker("BTC-GBP")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        swc = yf.Ticker("SWC.AQ")
        swc_price_gbp_pence = swc.info.get("currentPrice", 0) or 0
        swc_price = swc_price_gbp_pence / 100.0
        market_cap = swc.info.get("marketCap", None)
        if market_cap is None:
            market_cap = float("nan")

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * swc_price
        mnav_diluted = market_cap_fully_diluted / btc_nav if btc_nav else None

        # Étapes pour retrouver les 5.43 months :
        start_of_year = datetime(datetime.today().year, 1, 1)
        days_elapsed = (datetime.today() - start_of_year).days
        ytd_growth_factor = 1 + btc_yield_ytd / 100
        daily_yield = ytd_growth_factor ** (1 / days_elapsed) - 1

        ln_mnav = math.log(mnav_diluted)
        ln_yield = math.log(1 + daily_yield)
        days_to_cover = ln_mnav / ln_yield if ln_yield != 0 else None
        months_to_cover = days_to_cover / 30 if days_to_cover else None

        # Étapes pour retrouver le mois pour couvrir q2 based :
        q2_growth_factor = 1 + q2_yield / 100
        daily_yield_q2_based = q2_growth_factor ** (1 / 90) - 1

        ln_mnav_q2_based = math.log(mnav_diluted)
        ln_yield_q2_based = math.log(1 + daily_yield_q2_based)
        days_to_cover_q2_based = ln_mnav_q2_based / ln_yield_q2_based if ln_yield_q2_based != 0 else None
        months_to_cover_q2_based = days_to_cover_q2_based / 30 if days_to_cover_q2_based else None

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
        pcv = (mnav_diluted - 1) / months_to_cover if months_to_cover else None

        # Historique sur 2 jours (doit venir avant tout calcul basé dessus)
        btc_hist = btc.history(period="2d")["Close"]
        btc_price_yesterday = btc_hist.iloc[-2] if len(btc_hist) >= 2 else None
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None

        swc_hist = swc.history(period="2d")["Close"]
        swc_price_yesterday = swc_hist.iloc[-2] if len(swc_hist) >= 2 else None
        swc_price_yesterday_gbp = (swc_price_yesterday / 100.0) if swc_price_yesterday is not None else None
        swc_price_change_pct = (((swc_price - swc_price_yesterday_gbp) / swc_price_yesterday_gbp * 100) if swc_price_yesterday_gbp else None)

        # mNAV d’hier
        mnav_diluted_yesterday = (shares_fully_diluted * swc_price_yesterday_gbp) / (btc_price_yesterday * btc_held) if btc_price_yesterday and swc_price_yesterday_gbp else None
        mnav_diluted_change_pct = ((mnav_diluted - mnav_diluted_yesterday) / mnav_diluted_yesterday * 100) if mnav_diluted and mnav_diluted_yesterday else None

        # PCV d’hier + variation
        pcv_yesterday = (mnav_diluted_yesterday - 1) / months_to_cover if mnav_diluted_yesterday and months_to_cover else None
        pcv_change_pct = ((pcv - pcv_yesterday) / pcv_yesterday * 100) if pcv and pcv_yesterday else None

        btc_per_share = btc_held / shares_fully_diluted if shares_fully_diluted else None

        satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None

        btc_value_per_share_gbp = btc_per_share * btc_price if btc_per_share is not None else None

        invest_price = sum(entry["btc"] * entry["price"] for entry in btc_history)

        btc_gain = btc_nav - invest_price

        btc_torque = btc_nav / invest_price

        return jsonify({
            "btc_held": btc_held,
            "btc_yield_ytd": btc_yield_ytd,
            "q2_yield": q2_yield,
            "btc_price": round(btc_price, 2),
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,
            "swc_price": round(swc_price, 2),
            "swc_price_yesterday": swc_price_yesterday,
            "swc_price_yesterday_gbp": swc_price_yesterday_gbp,
            "btc_nav": round(btc_nav, 2),
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
            "market_cap": round(market_cap, 2) if market_cap and not math.isnan(market_cap) else None,
            "mnav_diluted": round(mnav_diluted, 3) if mnav_diluted else None,
            "daily_yield_pct": round(daily_yield * 100, 3),
            "days_to_cover": round(days_to_cover, 2) if days_to_cover else None,
            "pcv": round(pcv, 3) if pcv else None,
            "pcv_change_pct": round(pcv_change_pct, 2) if pcv_change_pct else None,
            "btc_yield_monthly_pct": round(btc_yield_monthly, 2) if btc_yield_monthly else None,
            "months_to_cover_q2_based": round(months_to_cover_q2_based, 2) if months_to_cover_q2_based else None,
            "btc_price_change_pct": round(btc_price_change_pct, 2) if btc_price_change_pct else None,
            "swc_price_change_pct": round(swc_price_change_pct, 2) if swc_price_change_pct else None,
            "mnav_diluted_change_pct": round(mnav_diluted_change_pct, 2) if mnav_diluted_change_pct else None,
            "shares_fully_diluted": shares_fully_diluted,
            "btc_history": btc_history,
            "btc_per_share": btc_per_share,
            "satoshi_per_share": satoshi_per_share,
            "btc_value_per_share_gbp": btc_value_per_share_gbp,
            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2),
            "btc_torque": btc_torque,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_swc_metrics():
    return get_metrics()
