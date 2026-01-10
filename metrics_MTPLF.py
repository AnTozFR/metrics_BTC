from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 1_434_392_925
    btc_held = 35102
    btc_yield_ytd = 496.4
    q2_yield = 11.9
    debt_btc = 0
    debt_fiat = 44_200_000_000

    btc_history = [
    {"date": "2024-04-23", "btc": 97.85, "price": 10220000},
    {"date": "2024-05-09", "btc": 19.87, "price": 10070000},
    {"date": "2024-06-10", "btc": 23.35, "price": 10710000},
    {"date": "2024-07-01", "btc": 20.20, "price": 9900000},
    {"date": "2024-07-08", "btc": 42.47, "price": 9420000},
    {"date": "2024-07-16", "btc": 21.88, "price": 9140000},
    {"date": "2024-07-22", "btc": 20.38, "price": 9810000},
    {"date": "2024-08-13", "btc": 57.10, "price": 8760000},
    {"date": "2024-08-20", "btc": 57.27, "price": 8730000},
    {"date": "2024-09-10", "btc": 38.46, "price": 7800000},
    {"date": "2024-10-01", "btc": 107.91, "price": 9270000},
    {"date": "2024-10-03", "btc": 23.97, "price": 8950000},
    {"date": "2024-10-07", "btc": 108.79, "price": 9190000},
    {"date": "2024-10-11", "btc": 109.00, "price": 9170000},
    {"date": "2024-10-15", "btc": 106.98, "price": 9350000},
    {"date": "2024-10-16", "btc": 5.91, "price": 9800000},
    {"date": "2024-10-28", "btc": 156.78, "price": 10210000},
    {"date": "2024-11-19", "btc": 124.12, "price": 14100000},
    {"date": "2024-12-23", "btc": 619.70, "price": 15330000},
    {"date": "2025-02-17", "btc": 269.43, "price": 14850000},
    {"date": "2025-02-20", "btc": 68.59, "price": 14530000},
    {"date": "2025-02-25", "btc": 135.00, "price": 14360000},
    {"date": "2025-03-03", "btc": 156.00, "price": 12950000},
    {"date": "2025-03-05", "btc": 497.00, "price": 13310000},
    {"date": "2025-03-12", "btc": 162.00, "price": 12390000},
    {"date": "2025-03-18", "btc": 150.00, "price": 12530000},
    {"date": "2025-03-24", "btc": 150.00, "price": 12570000},
    {"date": "2025-03-31", "btc": 696.00, "price": 14590000},
    {"date": "2025-04-02", "btc": 160.00, "price": 12490000},
    {"date": "2025-04-14", "btc": 319.00, "price": 11850000},
    {"date": "2025-04-21", "btc": 330.00, "price": 12180000},
    {"date": "2025-04-24", "btc": 145.00, "price": 13280000},
    {"date": "2025-05-07", "btc": 555.00, "price": 13820000},
    {"date": "2025-05-12", "btc": 1241.00, "price": 14850000},
    {"date": "2025-05-19", "btc": 1004.00, "price": 15130000},
    {"date": "2025-06-02", "btc": 1088.00, "price": 15520000},
    {"date": "2025-06-16", "btc": 1112.00, "price": 15180000},
    {"date": "2025-06-23", "btc": 1111.00, "price": 15540000},
    {"date": "2025-06-26", "btc": 1234.00, "price": 15620000},
    {"date": "2025-06-30", "btc": 1005.00, "price": 15570000},
    {"date": "2025-07-07", "btc": 2205.00, "price": 15640000},
    {"date": "2025-07-14", "btc": 797.00, "price": 17310000},
    {"date": "2025-07-28", "btc": 780.00, "price": 17520000},
    {"date": "2025-08-04", "btc": 463.00, "price": 17270000},
    {"date": "2025-08-12", "btc": 518.00, "price": 17540000},
    {"date": "2025-08-18", "btc": 775.00, "price": 17720000},
    {"date": "2025-08-24", "btc": 103.00, "price": 16860000},
    {"date": "2025-09-01", "btc": 1009.00, "price": 16330000},
    {"date": "2025-09-08", "btc": 136.00, "price": 15130000},
    {"date": "2025-09-22", "btc": 5419.00, "price": 17280000},
    {"date": "2025-09-30", "btc": 5268.00, "price": 17400000},
    {"date": "2025-12-30", "btc": 4279.00, "price": 16330000},
    ]

    try:
        # Données live
        btc = yf.Ticker("BTC-JPY")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        mtplf = yf.Ticker("3350.T")
        mtplf_price = mtplf.info.get("currentPrice", 0)

        shares_now_out = None
        try:
            sh = mtplf.get_shares_full(start="2025-01-01")
            if sh is not None and len(sh) > 0:
                sh = sh.dropna()
                try:
                    sh.index = sh.index.tz_localize(None)
                except:
                    pass
                sh = sh.sort_index()  # Ajoute pour tri
                shares_now_out = float(sh.iloc[-1])
        except:
            pass
        if shares_now_out is None:
            shares_now_out = mtplf.info.get('sharesOutstanding', None)
            if shares_now_out:
                shares_now_out = float(shares_now_out)
        # Puis pour market_cap :
        market_cap = shares_now_out * mtplf_price if shares_now_out and mtplf_price else mtplf.info.get('marketCap', 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * mtplf_price

        debt = debt_btc + debt_fiat
        enterprise_value = market_cap + debt
        enterprise_value_fully_diluted = market_cap_fully_diluted + debt

        mnav = enterprise_value / btc_nav if btc_nav else None
        mnav_diluted = enterprise_value_fully_diluted / btc_nav if btc_nav else None

        # --- Historiques sur 2 jours (même modèle que MSTR) ---
        btc_hist = btc.history(period="2d")["Close"]
        btc_price_yesterday = btc_hist.iloc[-2] if len(btc_hist) >= 2 else None
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None

        mtplf_hist = mtplf.history(period="2d")["Close"]
        mtplf_price_yesterday = mtplf_hist.iloc[-2] if len(mtplf_hist) >= 2 else None
        mtplf_price_change_pct = ((mtplf_price - mtplf_price_yesterday) / mtplf_price_yesterday * 100) if mtplf_price_yesterday else None

        # --- Timestamp de "hier" (défini AVANT de s'en servir) ---
        yday_dt = mtplf_hist.index[-2].to_pydatetime() if len(mtplf_hist) >= 2 else None

        # ---------- Série d'actions pour trouver "hier" ----------
        shares_series = None
        try:
            if 'sh' in locals() and sh is not None and len(sh) > 0:
                shares_series = sh
            else:
                tmp = mtplf.get_shares_full(start="2024-01-01")
                if tmp is not None and len(tmp) > 0:
                    tmp = tmp.dropna()
                    try:
                        tmp.index = tmp.index.tz_localize(None)
                    except Exception:
                        pass
                    tmp = tmp.sort_index()
                    shares_series = tmp
        except Exception:
            pass

        # Actions "hier" = dernière valeur <= close d’hier
        shares_yesterday = None
        if shares_series is not None and len(shares_series) > 0 and yday_dt is not None:
            for dt, val in shares_series.items():
                if dt.date() <= yday_dt.date():
                    shares_yesterday = float(val)
                else:
                    break
        # fallback
        if shares_yesterday is None:
            if shares_series is not None and len(shares_series) > 0:
                shares_yesterday = float(shares_series.iloc[-1])
            elif shares_now_out:
                shares_yesterday = float(shares_now_out)

        # Étapes pour retrouver le mois pour couvrir (même logique)
        q2_growth_factor = 1 + q2_yield / 100
        daily_yield_q2_based = q2_growth_factor ** (1 / 90) - 1

        ln_mnav_q2_based = math.log(mnav) if mnav and mnav > 0 else None
        ln_yield_q2_based = math.log(1 + daily_yield_q2_based) if daily_yield_q2_based is not None else None
        days_to_cover_q2_based = (ln_mnav_q2_based / ln_yield_q2_based) if (ln_mnav_q2_based and ln_yield_q2_based) else None
        months_to_cover_q2_based = (days_to_cover_q2_based / 30) if days_to_cover_q2_based else None

        ln_mnav_diluted_q2_based = math.log(mnav_diluted) if mnav_diluted and mnav_diluted > 0 else None
        days_to_cover_q2_based_diluted = (ln_mnav_diluted_q2_based / ln_yield_q2_based) if (ln_mnav_diluted_q2_based and ln_yield_q2_based) else None
        months_to_cover_q2_based_diluted = (days_to_cover_q2_based_diluted / 30) if days_to_cover_q2_based_diluted else None

        # Début du programme
        start_date = datetime.strptime("2020-08-10", "%Y-%m-%d")
        days_since_start = (datetime.today() - start_date).days
        btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

        today = datetime.today()
        months_elapsed = today.month - 1 + (1 if today.day >= 1 else 0)
        btc_yield_monthly = btc_yield_ytd / months_elapsed if months_elapsed > 0 else None

        # PCV
        pcv = (mnav - 1) / months_to_cover_q2_based if months_to_cover_q2_based else None

        # Hier (avec dette)
        market_cap_yesterday = (shares_yesterday * mtplf_price_yesterday) if (shares_yesterday and mtplf_price_yesterday) else None
        btc_nav_yesterday = (btc_price_yesterday * btc_held) if btc_price_yesterday else None
        enterprise_value_yesterday = (market_cap_yesterday + debt) if market_cap_yesterday else None
        mnav_yesterday = (enterprise_value_yesterday / btc_nav_yesterday) if (enterprise_value_yesterday and btc_nav_yesterday) else None
        mnav_change_pct = ((mnav - mnav_yesterday) / mnav_yesterday * 100) if (mnav and mnav_yesterday) else None

        # Par action
        btc_per_share = btc_held / shares_now_out if shares_now_out else None
        satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None
        btc_value_per_share_jpy = btc_per_share * btc_price if btc_per_share is not None else None

        # Coût d’acquisition & torque
        invest_price = sum(entry["btc"] * entry["price"] for entry in btc_history)
        btc_gain = btc_nav - invest_price
        btc_torque = btc_nav / invest_price

        return jsonify({
            "btc_held": btc_held,
            "debt": debt,
            "debt_btc": debt_btc,
            "debt_fiat": debt_fiat,
            "enterprise_value": enterprise_value,
            "btc_yield_ytd": btc_yield_ytd,
            "q2_yield": q2_yield,
            "btc_price": round(btc_price, 2),
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,
            "share_price": round(mtplf_price, 2),
            "btc_nav": round(btc_nav, 2),
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
            "market_cap": round(market_cap, 2),
            "mnav": round(mnav, 3) if mnav else None,
            "mnav_diluted": round(mnav_diluted, 3) if mnav_diluted else None,
            "pcv": round(pcv, 3) if pcv else None,
            "btc_yield_monthly_pct": round(btc_yield_monthly, 2) if btc_yield_monthly else None,
            "btc_price_change_pct": round(btc_price_change_pct, 2) if btc_price_change_pct else None,
            "share_price_change_pct": round(mtplf_price_change_pct, 2) if mtplf_price_change_pct else None,
            "mnav_change_pct": round(mnav_change_pct, 2) if mnav_change_pct else None,
            "shares_fully_diluted": shares_fully_diluted,
            "shares_now_out": shares_now_out,
            "btc_history": btc_history,
            "btc_per_share": btc_per_share,
            "satoshi_per_share": satoshi_per_share,
            "btc_value_per_share": btc_value_per_share_jpy,
            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2),
            "btc_torque": btc_torque,
            "months_to_cover_q2_based": round(months_to_cover_q2_based, 2) if months_to_cover_q2_based is not None else None,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_mtplf_metrics():
    return get_metrics()




















