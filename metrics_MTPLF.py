from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 885_942_925
    btc_held = 18888
    btc_yield_ytd = 480.2

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
    {"date": "2025-08-12", "btc": 518.00, "price": 118519},
    {"date": "2025-08-18", "btc": 775.00, "price": 120006}
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

        # ---------- BTC timeline cumulée ----------
        hist_sorted = sorted(btc_history, key=lambda e: e["date"])
        timeline = []
        cum = 0.0
        for e in hist_sorted:
            d = datetime.strptime(e["date"], "%Y-%m-%d")
            cum += float(e["btc"])
            timeline.append((d, cum))
        
        # ---------- Historique des actions (Yahoo) ----------
        basic_shares_series = None
        basic_shares_current = None
        shares_history_available = False  # flag debug
        
        # on veut couvrir largement 3 mois (download only)
        lookup_start = (timeline[-1][0] - timedelta(days=240)).strftime("%Y-%m-%d") if timeline else "2024-01-01"
        
        # on essaie d'abord la place japonaise (plus fiable), puis Frankfurt en fallback
        for ticker in (mtplf_japan, mtplf):
            try:
                sh = ticker.get_shares_full(start=lookup_start)
                if sh is not None and len(sh) > 0:
                    sh = sh.dropna()
                    try:
                        sh.index = sh.index.tz_localize(None)
                    except Exception:
                        pass
                    basic_shares_series = sh
                    basic_shares_current = float(sh.iloc[-1])
                    shares_history_available = True
                    break
            except Exception:
                pass
        
        # >>> PAS DE FALLBACK FULLY DILUTED <<<
        # Si pas d'historique Yahoo, on laissera les métriques "diluées" à None.
        
        # ---------- BTC Yield 3 mois (brut + dilué) + months_to_cover_3m ----------
        btc_yield_3m_pct = None
        btc_yield_3m_diluted_pct = None
        months_to_cover_3m = None
        
        cutoff_str = None  # pour debug optionnel
        shares_at_cutoff_out = None
        shares_now_out = None
        yahoo_first_point = None
        yahoo_last_point = None
        
        if timeline:
            last_date, holdings_now = timeline[-1]
            cutoff = last_date - timedelta(days=90)  # 3 mois = 90 jours
            cutoff_str = cutoff.strftime("%Y-%m-%d")
        
            # BTC à la cutoff: dernier cumul <= cutoff
            holdings_at_cutoff = 0.0
            for dt, h in timeline:
                if dt <= cutoff:
                    holdings_at_cutoff = h
                else:
                    break
        
            # ----- Version "brute" (sans dilution), si tu veux l'afficher aussi -----
            if holdings_at_cutoff > 0 and holdings_now >= holdings_at_cutoff:
                growth_factor_3m = holdings_now / holdings_at_cutoff
                btc_yield_3m_pct = (growth_factor_3m - 1.0) * 100.0
        
            # Actions à la cutoff: dernière valeur Yahoo ≤ cutoff (avec interpolation simple si possible)
            if shares_history_available:
                items = list(basic_shares_series.items())
                # Debug first/last point dates + valeurs
                try:
                    yahoo_first_point = {"date": items[0][0].strftime("%Y-%m-%d"), "shares": float(items[0][1])}
                    yahoo_last_point  = {"date": items[-1][0].strftime("%Y-%m-%d"), "shares": float(items[-1][1])}
                except Exception:
                    pass
        
                left = None
                right = None
                for dt, val in items:
                    if dt <= cutoff:
                        left = (dt, float(val))
                    elif dt > cutoff:
                        right = (dt, float(val))
                        break
        
                if left and right:
                    # interpolation temporelle à la date cutoff
                    (t0, v0), (t1, v1) = left, right
                    span = (t1 - t0).total_seconds()
                    w = (cutoff - t0).total_seconds() / span if span > 0 else 0.0
                    shares_at_cutoff = v0 + w * (v1 - v0)
                elif left:
                    shares_at_cutoff = left[1]
                elif right:
                    shares_at_cutoff = right[1]
                else:
                    shares_at_cutoff = None  # aucun point exploitable
        
                shares_at_cutoff_out = shares_at_cutoff
                shares_now_out = basic_shares_current
        
                # Yields dilué + months_to_cover_3m (uniquement si on a les 2 nombres d'actions)
                if (
                    holdings_at_cutoff > 0 and holdings_now >= holdings_at_cutoff and
                    shares_at_cutoff is not None and shares_at_cutoff > 0 and
                    basic_shares_current is not None and basic_shares_current > 0
                ):
                    dilution_factor_3m = basic_shares_current / shares_at_cutoff
                    btc_yield_3m_diluted_pct = (growth_factor_3m / dilution_factor_3m - 1.0) * 100.0
        
                    # Rendement quotidien basé sur le **facteur dilué** sur exactement 90 jours
                    days_window = max((last_date - cutoff).days, 1)  # ≈ 90, garanti ≥ 1
                    btc_per_share_factor_3m = (holdings_now / basic_shares_current) / (holdings_at_cutoff / shares_at_cutoff)
                    daily_yield_3m = btc_per_share_factor_3m ** (1.0 / days_window) - 1.0
        
                    if mn_nav and daily_yield_3m > -0.999999:
                        ln_mnav = math.log(mn_nav)
                        ln_yield_3m = math.log(1.0 + daily_yield_3m)
                        if ln_yield_3m != 0:
                            days_to_cover_3m = ln_mnav / ln_yield_3m
                            months_to_cover_3m = days_to_cover_3m / 30.0

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
            "btc_yield_3m_pct": round(btc_yield_3m_pct, 2) if btc_yield_3m_pct is not None else None,
            "btc_yield_3m_diluted_pct": round(btc_yield_3m_diluted_pct, 2) if btc_yield_3m_diluted_pct is not None else None,
            "months_to_cover_3m": round(months_to_cover_3m, 2) if months_to_cover_3m is not None else None,
            "cutoff": cutoff_str,  # <- au lieu de cutoff.strftime(...)
            "shares_at_cutoff": shares_at_cutoff_out,  # <- au lieu de shares_at_cutoff
            "shares_now": shares_now_out,
            "has_yahoo_series": basic_shares_series is not None,
            "yahoo_first_point": {
                "date": str(basic_shares_series.index[0].date()),
                "value": float(basic_shares_series.iloc[0])
            } if basic_shares_series is not None else None,
            "yahoo_last_point": {
                "date": str(basic_shares_series.index[-1].date()),
                "value": float(basic_shares_series.iloc[-1])
            } if basic_shares_series is not None else None,
        
            # (Optionnel) extra debug pour vérifier la cohérence
            "dilution_factor_3m": (shares_now_out / shares_at_cutoff_out) if shares_now_out and shares_at_cutoff_out else None,
            "btc_per_share_factor_3m": (
                (holdings_now / shares_now_out) / (holdings_at_cutoff / shares_at_cutoff_out)
            ) if (holdings_now and shares_now_out and holdings_at_cutoff and shares_at_cutoff_out) else None,
            "daily_yield_3m": daily_yield_3m if 'daily_yield_3m' in locals() else None,
            "days_window": days_window if 'days_window' in locals() else None,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_mtplf_metrics():
    return get_metrics()
