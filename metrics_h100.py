from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 352_950_000
    btc_held = 911.29
    btc_yield_ytd = 6013
    q2_yield = 1129
    debt_btc = 0
    debt_fiat = 30_719_716.92  # EUR

    btc_history = [
        {"date": "2025-05-22", "btc": 4.39,  "price": 110913},
        {"date": "2025-05-30", "btc": 1.85,  "price": 105178},
        {"date": "2025-06-05", "btc": 7.70,  "price": 105365},
        {"date": "2025-06-12", "btc": 10.46, "price": 109273},
        {"date": "2025-06-16", "btc": 144.80,"price": 108636},
        {"date": "2025-06-25", "btc": 31.01, "price": 107800},
        {"date": "2025-07-02", "btc": 47.33, "price": 107798},
        {"date": "2025-07-09", "btc": 46.93, "price": 108973},
        {"date": "2025-07-16", "btc": 75.53, "price": 116656},
        {"date": "2025-07-21", "btc": 140.25,"price": 118918},
        {"date": "2025-07-23", "btc": 117.93,"price": 117707},
        {"date": "2025-07-30", "btc": 56.90, "price": 117620},
        {"date": "2025-08-01", "btc": 17.47, "price": 116965},
        {"date": "2025-08-06", "btc": 60.60, "price": 115190},
        {"date": "2025-08-13", "btc": 45.80, "price": 119085},
        {"date": "2025-08-20", "btc": 102.19,"price": 120538}
    ]

    try:
        # Prix BTC (EUR)
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        # H100 Group (GS9.F)
        h100 = yf.Ticker("GS9.F")
        h100_price = h100.info.get("currentPrice", 0) or 0.0

        # ---------- Actions en circulation (basique) ----------
        shares_now_out = None
        try:
            sh = h100.get_shares_full(start="2025-01-01")
            if sh is not None and len(sh) > 0:
                sh = sh.dropna()
                try:
                    sh.index = sh.index.tz_localize(None)
                except Exception:
                    pass
                shares_now_out = float(sh.iloc[-1])
        except Exception:
            pass

        # ---------- Market caps (basique & fully diluted) ----------
        # Si Yahoo ne donne pas shares_now_out, repli sur marketCap si dispo.
        market_cap_info = h100.info.get("marketCap", None)
        market_cap = None
        if shares_now_out:
            market_cap = shares_now_out * h100_price
        elif market_cap_info:
            market_cap = float(market_cap_info)

        market_cap_fully_diluted = shares_fully_diluted * h100_price if h100_price else None

        # ---------- NAV (valeur BTC détenue) ----------
        btc_nav = btc_price * btc_held if btc_price else None

        # ---------- Enterprise Value (EV) ----------
        debt = debt_btc + debt_fiat
        enterprise_value = (market_cap + debt) if market_cap is not None else None
        enterprise_value_fully_diluted = (market_cap_fully_diluted + debt) if market_cap_fully_diluted is not None else None

        # ---------- mNAV (avec dette) ----------
        mnav = (enterprise_value / btc_nav) if (enterprise_value and btc_nav) else None
        mnav_diluted = (enterprise_value_fully_diluted / btc_nav) if (enterprise_value_fully_diluted and btc_nav) else None

        # ---------- “Months to cover” ----------
        # YTD-based (utilise la mnav_diluted par cohérence avec ta version précédente)
        start_of_year = datetime(datetime.today().year, 1, 1)
        days_elapsed = (datetime.today() - start_of_year).days or 1
        ytd_growth_factor = 1 + btc_yield_ytd / 100
        daily_yield_ytd_based = ytd_growth_factor ** (1 / days_elapsed) - 1

        months_to_cover_ytd_based = None
        if mnav_diluted and mnav_diluted > 0:
            ln_mnav_ytd_based = math.log(mnav_diluted)
            ln_yield_ytd_based = math.log(1 + daily_yield_ytd_based)
            days_to_cover_ytd_based = (ln_mnav_ytd_based / ln_yield_ytd_based) if ln_yield_ytd_based != 0 else None
            months_to_cover_ytd_based = (days_to_cover_ytd_based / 30) if days_to_cover_ytd_based else None

        # Q2-based (calcule basique + diluted)
        q2_growth_factor = 1 + q2_yield / 100
        daily_yield_q2_based = q2_growth_factor ** (1 / 90) - 1
        ln_yield_q2_based = math.log(1 + daily_yield_q2_based)

        months_to_cover_q2_based = None
        months_to_cover_q2_based_diluted = None
        if mnav and mnav > 0:
            days_to_cover_q2_based = math.log(mnav) / ln_yield_q2_based if ln_yield_q2_based != 0 else None
            months_to_cover_q2_based = (days_to_cover_q2_based / 30) if days_to_cover_q2_based else None
        if mnav_diluted and mnav_diluted > 0:
            days_to_cover_q2_based_diluted = math.log(mnav_diluted) / ln_yield_q2_based if ln_yield_q2_based != 0 else None
            months_to_cover_q2_based_diluted = (days_to_cover_q2_based_diluted / 30) if days_to_cover_q2_based_diluted else None

        # ---------- PCV (avec dette) ----------
        pcv = (mnav - 1) / months_to_cover_q2_based if months_to_cover_q2_based else None
        pcv_diluted = (mnav_diluted - 1) / months_to_cover_q2_based_diluted if months_to_cover_q2_based_diluted else None

        start_date = datetime.strptime("2025-05-22", "%Y-%m-%d")
        days_since_start = (datetime.today() - start_date).days
        btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

        # ---------- Historique prix pour variations ----------
        btc_hist = btc.history(period="2d")["Close"]
        btc_price_yesterday = btc_hist.iloc[-2] if len(btc_hist) >= 2 else None
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None

        h100_hist = h100.history(period="2d")["Close"]
        h100_price_yesterday = h100_hist.iloc[-2] if len(h100_hist) >= 2 else None
        h100_price_change_pct = ((h100_price - h100_price_yesterday) / h100_price_yesterday * 100) if h100_price_yesterday else None

        # Actions "hier" (réutilise la même série si dispo)
        shares_series = None
        try:
            if 'sh' in locals() and sh is not None and len(sh) > 0:
                shares_series = sh
            else:
                tmp = h100.get_shares_full(start="2025-01-01")
                if tmp is not None and len(tmp) > 0:
                    tmp = tmp.dropna()
                    try:
                        tmp.index = tmp.index.tz_localize(None)
                    except Exception:
                        pass
                    shares_series = tmp
        except Exception:
            pass

        shares_yesterday = None
        if shares_series is not None and len(shares_series) > 0 and h100_price_yesterday is not None:
            # on prend la dernière valeur connue (les séries Yahoo sont très peu fréquentes)
            shares_yesterday = float(shares_series.iloc[-1])

        # Market cap & EV d’hier (avec dette), puis mNAV d’hier
        market_cap_yesterday = (shares_yesterday * h100_price_yesterday) if (shares_yesterday and h100_price_yesterday) else None
        enterprise_value_yesterday = (market_cap_yesterday + debt) if market_cap_yesterday is not None else None
        btc_nav_yesterday = (btc_price_yesterday * btc_held) if btc_price_yesterday else None

        mnav_yesterday = (enterprise_value_yesterday / btc_nav_yesterday) if (enterprise_value_yesterday and btc_nav_yesterday) else None
        mnav_change_pct = ((mnav - mnav_yesterday) / mnav_yesterday * 100) if (mnav and mnav_yesterday) else None

        # Per share (basique si on a shares_now_out)
        btc_per_share = (btc_held / shares_now_out) if shares_now_out else None
        satoshi_per_share = (btc_per_share * 100_000_000) if btc_per_share is not None else None
        btc_value_per_share_eur = (btc_per_share * btc_price) if btc_per_share is not None else None

        # Coût cumulé & torque
        invest_price = sum(entry["btc"] * entry["price"] for entry in btc_history)
        btc_gain = (btc_nav - invest_price) if btc_nav is not None else None
        btc_torque = (btc_nav / invest_price) if invest_price else None

        return jsonify({
            "btc_held": btc_held,
            "debt": debt,
            "debt_btc": debt_btc,
            "debt_fiat": debt_fiat,

            "btc_yield_ytd": btc_yield_ytd,
            "q2_yield": q2_yield,
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,

            "btc_price": round(btc_price, 2),
            "share_price": round(h100_price, 2),

            "btc_nav": round(btc_nav, 2) if btc_nav is not None else None,

            "market_cap": round(market_cap, 2) if market_cap is not None else None,
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2) if market_cap_fully_diluted is not None else None,

            "enterprise_value": round(enterprise_value, 2) if enterprise_value is not None else None,
            "enterprise_value_fully_diluted": round(enterprise_value_fully_diluted, 2) if enterprise_value_fully_diluted is not None else None,

            "mnav": round(mnav, 3) if mnav else None,
            "mnav_diluted": round(mnav_diluted, 3) if mnav_diluted else None,
            "mnav_change_pct": round(mnav_change_pct, 2) if mnav_change_pct else None,

            "months_to_cover_q2_based": round(months_to_cover_q2_based, 2) if months_to_cover_q2_based else None,
            "months_to_cover_q2_based_diluted": round(months_to_cover_q2_based_diluted, 2) if months_to_cover_q2_based_diluted else None,

            "pcv": round(pcv, 3) if pcv else None,
            "pcv_diluted": round(pcv_diluted, 3) if pcv_diluted else None,

            "btc_price_change_pct": round(btc_price_change_pct, 2) if btc_price_change_pct else None,
            "share_price_change_pct": round(h100_price_change_pct, 2) if h100_price_change_pct else None,

            "shares_fully_diluted": shares_fully_diluted,
            "shares_now_out": shares_now_out,

            "btc_history": btc_history,
            "btc_per_share": btc_per_share,
            "satoshi_per_share": satoshi_per_share,
            "btc_value_per_share_eur": btc_value_per_share_eur,

            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2) if btc_gain is not None else None,
            "btc_torque": btc_torque,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_h100_metrics():
    return get_metrics()
