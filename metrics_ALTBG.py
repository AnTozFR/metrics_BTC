from flask import Flask, jsonify 
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import math

def get_metrics():
    # Données fixes
    shares_fully_diluted = 331_180_647
    btc_held = 2201
    btc_yield_ytd = 1519.5
    q2_yield = 69

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
    {"date": "2025-08-11", "btc": 126, "price": 98746}
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
        {"date": "2025-07-21", "type": "ATM Type", "detail": "TOBAM (4.1039€/share)  - ATM Type #6", "montant": 1.6},
        {"date": "2025-07-21", "type": "Reserved capital increase", "detail": "Peak Hodl Ltd (3.4693€/share)", "montant": 8.7}
    ]

    capital_data = {
        "labels": [
            "Fulgur Ventures",
            "Public & Institutional",
            "Adam Back",
            "Dirigeants",
            "TOBAM",
            "UTXO Management",
            "Peak Hodl Ltd",
            "Actions gratuites"
        ],
        "values": [
            145_911_009,
            103_249_822,
            36_412_138,
            18_418_953,
            14_809_515,
            7_999_210,
            2_500_000,
            1_880_000
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
        mnav_diluted = market_cap_fully_diluted / btc_nav if btc_nav else None

        # --- BTC cumulés (timeline) ---
        hist_sorted = sorted(btc_history, key=lambda e: e["date"])
        timeline = []
        cum_hold = 0.0
        for e in hist_sorted:
            d = datetime.strptime(e["date"], "%Y-%m-%d")
            cum_hold += float(e["btc"])
            timeline.append((d, cum_hold))

        btc_yield_3m_pct = None
        btc_yield_3m_diluted_pct = None
        months_to_cover_3m = None

        # ================================
        # Historique des actions (Yahoo)
        # ================================
        basic_shares_series = None
        basic_shares_current = None

        # Petite marge (120j) pour couvrir > 90j
        lookup_start = (timeline[-1][0] - timedelta(days=120)).strftime("%Y-%m-%d") if timeline else "2024-01-01"
        try:
            sh = altbg.get_shares_full(start=lookup_start)
            if sh is not None and len(sh) > 0:
                sh = sh.dropna()
                try:
                    sh.index = sh.index.tz_localize(None)
                except Exception:
                    pass
                basic_shares_series = sh
                basic_shares_current = float(sh.iloc[-1])
        except Exception:
            pass

        # Fallback : somme de ton capital si pas d'historique Yahoo
        if basic_shares_current is None:
            basic_shares_current = float(sum(capital_data["values"]))
            basic_shares_series = None  # pas d'historique précis

        # ================================
        # BTC Yield 3 mois (brut + dilué)
        # ================================
        btc_per_share_now = None
        btc_per_share_3m = None
        basic_shares_cutoff_3m = None

        if timeline:
            last_date, holdings_now = timeline[-1]
            cutoff = last_date - timedelta(days=90)

            # BTC à la date de cutoff (dernier cumul <= cutoff)
            holdings_at_cutoff = 0.0
            for dt, hold in timeline:
                if dt <= cutoff:
                    holdings_at_cutoff = hold
                else:
                    break

            # Actions à la date de cutoff
            shares_at_cutoff = basic_shares_current
            if basic_shares_series is not None and len(basic_shares_series) > 0:
                # prendre la dernière valeur <= cutoff
                eligible = [(dt, val) for dt, val in basic_shares_series.items() if dt <= cutoff]
                if eligible:
                    shares_at_cutoff = float(eligible[-1][1])

            basic_shares_cutoff_3m = shares_at_cutoff

            # Yields
            if holdings_at_cutoff > 0 and holdings_now >= holdings_at_cutoff and shares_at_cutoff > 0 and basic_shares_current > 0:
                growth_factor_3m = holdings_now / holdings_at_cutoff
                dilution_factor_3m = basic_shares_current / shares_at_cutoff

                # BTC Yield "brut" (sans dilution)
                btc_yield_3m_pct = (growth_factor_3m - 1.0) * 100.0

                # BTC Yield "dilué" = évolution de (BTC / action)
                btc_yield_3m_diluted_pct = (growth_factor_3m / dilution_factor_3m - 1.0) * 100.0

                # BTC/share now & cutoff (pratique pour debugging / affichage)
                btc_per_share_now = holdings_now / basic_shares_current
                btc_per_share_3m = holdings_at_cutoff / shares_at_cutoff

                # Estimation months_to_cover_3m basée sur le **yield dilué 3 mois** (BTC par action)
                window_start = max(cutoff, timeline[0][0])
                days_window = max((last_date - window_start).days, 1)
                
                # Facteur de croissance sur 3 mois **par action** (dilué)
                btc_per_share_factor_3m = (holdings_now / basic_shares_current) / (holdings_at_cutoff / shares_at_cutoff)
                
                # Rendement quotidien moyen dérivé du facteur dilué
                daily_yield_3m = btc_per_share_factor_3m ** (1.0 / days_window) - 1.0
                
                if mnav_diluted and daily_yield_3m > -0.999999:
                    ln_mnav = math.log(mnav_diluted)
                    ln_yield_3m = math.log(1.0 + daily_yield_3m)
                    if ln_yield_3m != 0:
                        days_to_cover_3m = ln_mnav / ln_yield_3m
                        months_to_cover_3m = days_to_cover_3m / 30.0
                        
        # Étapes pour retrouver les 5.43 months :
        start_of_year = datetime(datetime.today().year, 1, 1)
        days_elapsed = (datetime.today() - start_of_year).days
        ytd_growth_factor = 1 + btc_yield_ytd / 100
        daily_yield = ytd_growth_factor ** (1 / days_elapsed) - 1

        ln_mnav = math.log(mnav_diluted)
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
        pcv = (mnav_diluted - 1) / months_to_cover if months_to_cover else None

        # Historique sur 2 jours (doit venir avant tout calcul basé dessus)
        btc_hist = btc.history(period="2d")["Close"]
        btc_price_yesterday = btc_hist.iloc[-2] if len(btc_hist) >= 2 else None
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None

        altbg_hist = altbg.history(period="2d")["Close"]
        altbg_price_yesterday = altbg_hist.iloc[-2] if len(altbg_hist) >= 2 else None
        altbg_price_change_pct = ((altbg_price - altbg_price_yesterday) / altbg_price_yesterday * 100) if altbg_price_yesterday else None

        # mNAV d’hier
        mnav_diluted_yesterday = (shares_fully_diluted * altbg_price_yesterday) / (btc_price_yesterday * btc_held) if btc_price_yesterday and altbg_price_yesterday else None
        mnav_diluted_change_pct = ((mnav_diluted - mnav_diluted_yesterday) / mnav_diluted_yesterday * 100) if mnav_diluted and mnav_diluted_yesterday else None

        # PCV d’hier + variation
        pcv_yesterday = (mnav_diluted_yesterday - 1) / months_to_cover if mnav_diluted_yesterday and months_to_cover else None
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
            "mnav_diluted": round(mnav_diluted, 3) if mnav_diluted else None,
            "daily_yield_pct": round(daily_yield * 100, 3),
            "days_to_cover": round(days_to_cover, 2) if days_to_cover else None,
            "pcv": round(pcv, 3) if pcv else None,
            "pcv_change_pct": round(pcv_change_pct, 2) if pcv_change_pct else None,
            "btc_yield_monthly_pct": round(btc_yield_monthly, 2) if btc_yield_monthly else None,
            "months_to_cover": round(months_to_cover, 2) if months_to_cover else None,
            "btc_price_change_pct": round(btc_price_change_pct, 2) if btc_price_change_pct else None,
            "altbg_price_change_pct": round(altbg_price_change_pct, 2) if altbg_price_change_pct else None,
            "mnav_diluted_change_pct": round(mnav_diluted_change_pct, 2) if mnav_diluted_change_pct else None,
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
            "btc_yield_3m_diluted_pct": round(btc_yield_3m_diluted_pct, 2) if btc_yield_3m_diluted_pct is not None else None,
            "months_to_cover_3m": round(months_to_cover_3m, 2) if months_to_cover_3m is not None else None,
            "cutoff": cutoff.strftime("%Y-%m-%d"),
            "shares_at_cutoff": shares_at_cutoff,
            "shares_now": basic_shares_current,
            "has_yahoo_series": basic_shares_series is not None,
            "yahoo_first_point": {
            "date": str(basic_shares_series.index[0].date()),
            "value": float(basic_shares_series.iloc[0])
                } if basic_shares_series is not None else None,
            "yahoo_last_point": {
            "date": str(basic_shares_series.index[-1].date()),
            "value": float(basic_shares_series.iloc[-1])
                } if basic_shares_series is not None else None,
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_altbg_metrics():
    return get_metrics()

