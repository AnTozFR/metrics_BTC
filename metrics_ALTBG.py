from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 335_949_647
    btc_held = 2249
    btc_yield_ytd = 1536.6
    q2_yield = 69
    debt_btc = 115_900_000
    debt_fiat = 0

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
    {"date": "2025-07-14", "btc": 29, "price": 95225},
    {"date": "2025-07-21", "btc": 22, "price": 101112},
    {"date": "2025-07-28", "btc": 58, "price": 102211},
    {"date": "2025-08-05", "btc": 62, "price": 99889},
    {"date": "2025-08-11", "btc": 126, "price": 98746},
    {"date": "2025-09-15", "btc": 48, "price": 98575},
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
        {"date": "2025-07-21", "type": "ATM Type", "detail": "TOBAM (4.1039€/share) - ATM Type #6", "montant": 1.6},
        {"date": "2025-07-21", "type": "Reserved capital increase", "detail": "Peak Hodl Ltd (3.4693€/share)", "montant": 8.7},
        {"date": "2025-08-04", "type": "Capital increase", "detail": "TOBAM Bitcoin Alpha Fund (2.904€/share)", "montant": 5},
        {"date": "2025-08-04", "type": "OCA A-05 Tranche 1", "detail": "TOBAM Bitcoin Alpha Fund (3.6557€/share)", "montant": 6.5},
        {"date": "2025-08-18", "type": "Capital increase", "detail": "Adam Back (2.238€/share)", "montant": 2.2},
        {"date": "2025-09-08", "type": "ATM Type", "detail": "TOBAM (1.72€/share) - ATM Type #7", "montant": 1.8},
        {"date": "2025-09-08", "type": "Capital increase", "detail": "Fulgur Ventures (0.544€/share, OCA B-01 adjustment)", "montant": 0.7},
        {"date": "2025-09-08", "type": "Reserved capital increase", "detail": "TOBAM Bitcoin Alpha Fund (1.69€/share)", "montant": 2.5},
        {"date": "2025-09-20", "type": "Capital increase", "detail": "Private placement at 1.55€/share (58.1 M€) – Capital B – potential acquisition of ~500 BTC", "montant": 58.1},
    ]

    capital_data = {
        "labels": [
            "Fulgur Ventures",
            "Public & Institutional",
            "Adam Back",
            "Dirigeants",
            "TOBAM",
            "UTXO Management",
            "Peak Hodl Ltd"
        ],
        "values": [
            147_161_009,
            105_329_656,
            37_412_138,
            20_298_953,
            15_248_681,
            7_999_210,
            2_500_000
        ]
    }

    try:
        # Données live
        btc = yf.Ticker("BTC-EUR")
        btc_price = btc.history(period="1d")["Close"].iloc[-1]

        altbg = yf.Ticker("ALCPB.PA")
        altbg_price = altbg.info.get("currentPrice", 0)
        market_cap = altbg.info.get("marketCap", 0)

        # NAV & mNAV
        btc_nav = btc_price * btc_held
        market_cap_fully_diluted = shares_fully_diluted * altbg_price

        debt = debt_btc + debt_fiat
        enterprise_value = market_cap + debt
        enterprise_value_fully_diluted = market_cap_fully_diluted + debt
        
        mnav = enterprise_value / btc_nav if btc_nav else None
        mnav_diluted = enterprise_value_fully_diluted / btc_nav if btc_nav else None

        # ---------- Récupération du nombre d'actions en circulation (Yahoo) ----------
        shares_now_out = None
        try:
            sh = altbg.get_shares_full(start="2024-01-01")
            if sh is not None and len(sh) > 0:
                sh = sh.dropna()
                try:
                    sh.index = sh.index.tz_localize(None)
                except Exception:
                    pass
                shares_now_out = float(sh.iloc[-1])  # dernière valeur = actions en circulation actuelles
        except Exception:
            pass  # si Yahoo ne renvoie rien, shares_now_out restera None
                   
        # Étapes pour retrouver le mois pour couvrir ytd based :
        start_of_year = datetime(datetime.today().year, 1, 1)
        days_elapsed = (datetime.today() - start_of_year).days
        ytd_growth_factor = 1 + btc_yield_ytd / 100
        daily_yield_ytd_based = ytd_growth_factor ** (1 / days_elapsed) - 1

        ln_mnav_ytd_based = math.log(mnav)
        ln_yield_ytd_based = math.log(1 + daily_yield_ytd_based)
        days_to_cover_ytd_based = ln_mnav_ytd_based / ln_yield_ytd_based if ln_yield_ytd_based != 0 else None
        months_to_cover_ytd_based = days_to_cover_ytd_based / 30 if days_to_cover_ytd_based else None

        # Étapes pour retrouver le mois pour couvrir q2 based :
        q2_growth_factor = 1 + q2_yield / 100
        daily_yield_q2_based = q2_growth_factor ** (1 / 90) - 1

        ln_mnav_q2_based = math.log(mnav)
        ln_yield_q2_based = math.log(1 + daily_yield_q2_based)
        days_to_cover_q2_based = ln_mnav_q2_based / ln_yield_q2_based if ln_yield_q2_based != 0 else None
        months_to_cover_q2_based = days_to_cover_q2_based / 30 if days_to_cover_q2_based else None
        
        # Début du programme
        start_date = datetime.strptime("2024-11-05", "%Y-%m-%d")
        days_since_start = (datetime.today() - start_date).days

        # Vitesse d'accumulation linéaire
        btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

        # Nombre de mois entiers écoulés depuis le début de l'année
        today = datetime.today()
        months_elapsed = today.month - 1 + (1 if today.day >= 1 else 0)  # +1 si on veut inclure le mois en cours

        # PCV
        pcv = (mnav - 1) / months_to_cover_q2_based if months_to_cover_q2_based else None

        # Historique sur 2 jours (doit venir avant tout calcul basé dessus)
        btc_hist = btc.history(period="2d")["Close"]
        btc_price_yesterday = btc_hist.iloc[-2] if len(btc_hist) >= 2 else None
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None

        altbg_hist = altbg.history(period="2d")["Close"]
        altbg_price_yesterday = altbg_hist.iloc[-2] if len(altbg_hist) >= 2 else None
        altbg_price_change_pct = ((altbg_price - altbg_price_yesterday) / altbg_price_yesterday * 100) if altbg_price_yesterday else None
        

        # --- Timestamp de "hier" côté action (même index que altbg_hist) ---
        yday_dt = altbg_hist.index[-2].to_pydatetime() if len(altbg_hist) >= 2 else None
        
        # --- Récupérer/rafraîchir la série d'actions si besoin ---
        shares_series = None
        try:
            # réutilise sh si déjà chargé ci-dessus
            if 'sh' in locals() and sh is not None and len(sh) > 0:
                shares_series = sh
            else:
                tmp = altbg.get_shares_full(start="2024-01-01")
                if tmp is not None and len(tmp) > 0:
                    tmp = tmp.dropna()
                    try:
                        tmp.index = tmp.index.tz_localize(None)
                    except Exception:
                        pass
                    shares_series = tmp
        except Exception:
            pass
        
        # --- Actions "hier" = dernière valeur <= close d’hier ---
        shares_yesterday = None
        if shares_series is not None and len(shares_series) > 0 and yday_dt is not None:
            for dt, val in shares_series.items():
                if dt.date() <= yday_dt.date():
                    shares_yesterday = float(val)
                else:
                    break
        # fallback: si rien avant hier, prends la dernière connue
        if shares_yesterday is None and shares_series is not None and len(shares_series) > 0:
            shares_yesterday = float(shares_series.iloc[-1])
        
        # --- Market cap "hier" + mNAV "hier" (non diluée) ---
        # 3) Hier (inclure la dette dans l'EV d'hier)
        market_cap_yesterday = (shares_yesterday * altbg_price_yesterday) if (shares_yesterday and altbg_price_yesterday) else None
        btc_nav_yesterday = (btc_price_yesterday * btc_held) if btc_price_yesterday else None
        enterprise_value_yesterday = (market_cap_yesterday + debt) if market_cap_yesterday else None
        
        mnav_yesterday = (enterprise_value_yesterday / btc_nav_yesterday) if (enterprise_value_yesterday and btc_nav_yesterday) else None
        mnav_change_pct = ((mnav - mnav_yesterday) / mnav_yesterday * 100) if (mnav and mnav_yesterday) else None

        btc_per_share = btc_held / shares_now_out if shares_now_out else None

        satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None

        btc_value_per_share_eur = btc_per_share * btc_price if btc_per_share is not None else None

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
            "share_price": round(altbg_price, 2),
            "btc_nav": round(btc_nav, 2),
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
            "market_cap": round(market_cap, 2),
            "mnav_diluted": round(mnav_diluted, 3) if mnav_diluted else None,
            "mnav": round(mnav, 3) if mnav else None,
            "days_to_cover_q2_based": round(days_to_cover_q2_based, 2) if days_to_cover_q2_based else None,
            "pcv": round(pcv, 3) if pcv else None,
            "months_to_cover_q2_based": round(months_to_cover_q2_based, 2) if months_to_cover_q2_based else None,
            "btc_price_change_pct": round(btc_price_change_pct, 2) if btc_price_change_pct else None,
            "share_price_change_pct": round(altbg_price_change_pct, 2) if altbg_price_change_pct else None,
            "mnav_change_pct": round(mnav_change_pct, 2) if mnav_change_pct else None,
            "shares_fully_diluted": shares_fully_diluted,
            "btc_history": btc_history,
            "fundraising_data": fundraising_data,
            "capital_data": capital_data,
            "btc_per_share": btc_per_share,
            "satoshi_per_share": satoshi_per_share,
            "btc_value_per_share": btc_value_per_share_eur,
            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2),
            "btc_torque": btc_torque,
            "shares_now_out": shares_now_out,
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_altbg_metrics():
    return get_metrics()























