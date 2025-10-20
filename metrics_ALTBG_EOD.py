from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import math
import os

EODHD_API_TOKEN = os.getenv('EODHD_API_TOKEN')
if not EODHD_API_TOKEN:
    raise ValueError("EODHD_API_TOKEN environment variable is required.")

EODHD_BASE_URL = 'https://eodhd.com/api'

def fetch_eodhd_data(endpoint, params=None):
    """Helper to fetch data from EODHD API with error handling."""
    url = EODHD_BASE_URL + endpoint
    all_params = {'api_token': EODHD_API_TOKEN, 'fmt': 'json'}
    if params:
        all_params.update(params)
    try:
        response = requests.get(url, params=all_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and not data:
            print(f"Empty data for {endpoint}")
            return None
        print(f"Success for {endpoint}: {len(data) if isinstance(data, list) else 'dict'} items")
        return data
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

def get_metrics():
    # Données fixes (inchangées)
    shares_fully_diluted = 389_824_422
    btc_held = 2812
    btc_yield_ytd = 1651.2
    q2_yield = 28.1
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
        {"date": "2025-09-22", "btc": 551, "price": 99272},
        {"date": "2025-09-29", "btc": 12, "price": 95900},
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
            155_588_780,
            148_671_191,
            37_412_138,
            21_873_863,
            15_248_681,
            8_529_769,
            2_500_000
        ]
    }

    try:
        today = datetime.today()
        end_date = today.strftime('%Y-%m-%d')
        start_hist = (today - timedelta(days=3)).strftime('%Y-%m-%d')  # Buffer for 2 days

        # BTC-USD EOD history (2 days) + EURUSD for conversion to EUR
        btc_usd_hist = fetch_eodhd_data('/eod/BTC-USD.CC', {'period': 'd', 'from': start_hist, 'to': end_date})
        eur_usd_hist = fetch_eodhd_data('/eod/EURUSD.FOREX', {'period': 'd', 'from': start_hist, 'to': end_date})
        # ALCPB.PA EOD history (2 days)
        altbg_hist_data = fetch_eodhd_data('/eod/ALCPB.PA', {'period': 'd', 'from': start_hist, 'to': end_date})
        # Fundamentals for ALCPB.PA (shares, market cap) - fallback if 403
        altbg_fund = fetch_eodhd_data('/fundamentals/ALCPB.PA')

        # Extract & convert BTC to EUR
        btc_price = None
        btc_price_yesterday = None
        eur_usd_rate = 1.0  # Fallback 1 USD = 1 EUR
        eur_usd_yesterday = 1.0
        altbg_price = None
        altbg_price_yesterday = None
        yday_dt = None

        if btc_usd_hist and len(btc_usd_hist) >= 2:
            btc_usd_today = float(btc_usd_hist[-1]['close'])
            btc_usd_yest = float(btc_usd_hist[-2]['close'])
            # Convert today
            if eur_usd_hist and len(eur_usd_hist) >= 1:
                eur_usd_rate = float(eur_usd_hist[-1]['close'])
            btc_price = btc_usd_today / eur_usd_rate if eur_usd_rate > 0 else None
            # Convert yesterday
            if len(eur_usd_hist) >= 2:
                eur_usd_yesterday = float(eur_usd_hist[-2]['close'])
            btc_price_yesterday = btc_usd_yest / eur_usd_yesterday if eur_usd_yesterday > 0 else None

        if altbg_hist_data and len(altbg_hist_data) >= 2:
            altbg_price = float(altbg_hist_data[-1]['close'])
            altbg_price_yesterday = float(altbg_hist_data[-2]['close'])
            yday_str = altbg_hist_data[-2]['date']
            yday_dt = datetime.strptime(yday_str, '%Y-%m-%d').date()

        # Shares from fundamentals (current) - fallback to fully_diluted if None
        shares_now_out = None
        shares_yesterday = None
        if altbg_fund and 'General' in altbg_fund:
            shares_now_out = float(altbg_fund['General'].get('SharesOutstanding', shares_fully_diluted))
        else:
            shares_now_out = shares_fully_diluted  # Fallback approx
        shares_yesterday = shares_now_out  # Simplified; historical shares would require quarterly parse

        market_cap = float(altbg_fund['General'].get('market_cap_basic', 0)) if altbg_fund and 'General' in altbg_fund else (shares_now_out * altbg_price if shares_now_out and altbg_price else 0)

        # NAV & mNAV (fallback enterprise_value to debt if no market_cap)
        btc_nav = btc_price * btc_held if btc_price else None
        market_cap_fully_diluted = shares_fully_diluted * altbg_price if altbg_price else None
        debt = debt_btc + debt_fiat
        enterprise_value = market_cap + debt if market_cap else debt  # Fallback sans market_cap
        enterprise_value_fully_diluted = market_cap_fully_diluted + debt if market_cap_fully_diluted else enterprise_value
        
        mnav = enterprise_value / btc_nav if btc_nav and enterprise_value and btc_nav != 0 else None
        mnav_diluted = enterprise_value_fully_diluted / btc_nav if btc_nav and enterprise_value_fully_diluted and btc_nav != 0 else None

        # YTD based (guards renforcés)
        start_of_year = datetime(today.year, 1, 1)
        days_elapsed = (today - start_of_year).days
        ytd_growth_factor = 1 + btc_yield_ytd / 100
        daily_yield_ytd_based = ytd_growth_factor ** (1 / days_elapsed) - 1 if days_elapsed > 0 else None

        ln_mnav_ytd_based = math.log(mnav) if mnav and mnav > 0 else None
        ln_yield_ytd_based = math.log(1 + daily_yield_ytd_based) if daily_yield_ytd_based is not None else None
        days_to_cover_ytd_based = ln_mnav_ytd_based / ln_yield_ytd_based if ln_mnav_ytd_based is not None and ln_yield_ytd_based and ln_yield_ytd_based != 0 else None
        months_to_cover_ytd_based = days_to_cover_ytd_based / 30 if days_to_cover_ytd_based else None

        # Q2 based (guards renforcés)
        q2_growth_factor = 1 + q2_yield / 100
        daily_yield_q2_based = q2_growth_factor ** (1 / 90) - 1

        ln_mnav_q2_based = math.log(mnav) if mnav and mnav > 0 else None
        ln_yield_q2_based = math.log(1 + daily_yield_q2_based) if daily_yield_q2_based > -1 else None
        days_to_cover_q2_based = ln_mnav_q2_based / ln_yield_q2_based if ln_mnav_q2_based is not None and ln_yield_q2_based and ln_yield_q2_based != 0 else None
        months_to_cover_q2_based = days_to_cover_q2_based / 30 if days_to_cover_q2_based else None
        
        # Program start
        start_date = datetime.strptime("2024-11-05", "%Y-%m-%d")
        days_since_start = (today - start_date).days
        btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

        months_elapsed = today.month - 1 + (1 if today.day >= 1 else 0)

        # PCV (guard renforcé)
        pcv = (mnav - 1) / months_to_cover_q2_based if mnav is not None and months_to_cover_q2_based and months_to_cover_q2_based != 0 else None

        # Price changes
        btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday and btc_price_yesterday != 0 else None
        altbg_price_change_pct = ((altbg_price - altbg_price_yesterday) / altbg_price_yesterday * 100) if altbg_price_yesterday and altbg_price_yesterday != 0 else None
        
        # Yesterday mNAV (fallback enterprise_value_yesterday to debt)
        market_cap_yesterday = (shares_yesterday * altbg_price_yesterday) if shares_yesterday and altbg_price_yesterday else None
        btc_nav_yesterday = (btc_price_yesterday * btc_held) if btc_price_yesterday else None
        enterprise_value_yesterday = (market_cap_yesterday + debt) if market_cap_yesterday else debt
        
        mnav_yesterday = enterprise_value_yesterday / btc_nav_yesterday if btc_nav_yesterday and enterprise_value_yesterday and btc_nav_yesterday != 0 else None
        mnav_change_pct = ((mnav - mnav_yesterday) / mnav_yesterday * 100) if mnav and mnav_yesterday and mnav_yesterday != 0 else None

        btc_per_share = btc_held / shares_now_out if shares_now_out else None

        satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None

        btc_value_per_share_eur = btc_per_share * btc_price if btc_per_share is not None and btc_price else None

        invest_price = sum(entry["btc"] * entry["price"] for entry in btc_history)

        btc_gain = btc_nav - invest_price if btc_nav else None

        btc_torque = btc_nav / invest_price if invest_price and btc_nav and invest_price != 0 else None

        return jsonify({
            "btc_held": btc_held,
            "debt": debt,
            "debt_btc": debt_btc,
            "debt_fiat": debt_fiat,
            "enterprise_value": enterprise_value,
            "btc_yield_ytd": btc_yield_ytd,
            "q2_yield": q2_yield,
            "btc_price": round(btc_price, 2) if btc_price else None,
            "btc_per_day": round(btc_per_day, 3) if btc_per_day else None,
            "share_price": round(altbg_price, 2) if altbg_price else None,
            "btc_nav": round(btc_nav, 2) if btc_nav else None,
            "market_cap_fully_diluted": round(market_cap_fully_diluted, 2) if market_cap_fully_diluted else None,
            "market_cap": round(market_cap, 2) if market_cap else None,
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
            "btc_value_per_share": round(btc_value_per_share_eur, 2) if btc_value_per_share_eur else None,
            "invest_price": round(invest_price, 2),
            "btc_gain": round(btc_gain, 2) if btc_gain else None,
            "btc_torque": round(btc_torque, 4) if btc_torque else None,
            "shares_now_out": shares_now_out,
        })

    except Exception as e:
        print(f"Unexpected error in get_metrics: {e}")  # Log pour Render
        return jsonify({"error": str(e)}), 500

def get_altbg_eod_metrics():
    return get_metrics()
