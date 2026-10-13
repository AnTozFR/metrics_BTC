from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math
import time

# ---------------------------------------------------------------------------
# Cache serveur : évite d'appeler Yahoo à chaque requête du front
# (le front rafraîchit toutes les 15 s, pour chaque visiteur).
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 120
_cache = {"ts": 0.0, "data": None}

# Si Yahoo renvoie un nombre d'actions faux ou périmé, renseigne ici le nombre
# d'actions en circulation publié par Capital B (ex : 382_000_000).
# Laisser à None pour utiliser la valeur Yahoo.
SHARES_OUTSTANDING_MANUAL = None


def _last_two_closes(ticker, period="5d"):
    """Dernier cours + cours de la veille via l'endpoint 'chart' (pas de crumb requis)."""
    hist = ticker.history(period=period, auto_adjust=False)
    if hist is None or hist.empty:
        return None, None, None
    closes = hist["Close"].dropna()
    if closes.empty:
        return None, None, None
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    prev_dt = closes.index[-2].to_pydatetime() if len(closes) >= 2 else None
    return last, prev, prev_dt


def _shares_series(ticker):
    """Historique du nombre d'actions en circulation (Yahoo), nettoyé."""
    try:
        sh = ticker.get_shares_full(start="2024-01-01")
        if sh is None or len(sh) == 0:
            return None
        sh = sh.dropna()
        try:
            sh.index = sh.index.tz_localize(None)
        except Exception:
            pass
        sh = sh[~sh.index.duplicated(keep="last")].sort_index()
        return sh if len(sh) > 0 else None
    except Exception:
        return None


def _days_to_cover(mnav, daily_yield):
    if not mnav or mnav <= 0 or not daily_yield or daily_yield <= 0:
        return None
    ln_yield = math.log(1 + daily_yield)
    return math.log(mnav) / ln_yield if ln_yield != 0 else None


def _round(value, ndigits):
    return round(value, ndigits) if value is not None else None


def _compute_metrics():
    # Données fixes
    shares_fully_diluted = 47_524_921
    btc_held = 3538
    btc_yield_ytd = 2.2
    q2_yield = 1.1
    debt_btc_amount = 821  # dette de Capital B exprimée en nombre de BTC
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
        {"date": "2025-10-20", "btc": 6, "price": 96231},
        {"date": "2025-11-25", "btc": 5, "price": 88968},
        {"date": "2026-02-09", "btc": 5, "price": 64124},
        {"date": "2026-02-16", "btc": 6, "price": 55270},
        {"date": "2026-03-09", "btc": 2, "price": 61660},
        {"date": "2026-03-16", "btc": 8, "price": 60934},
        {"date": "2026-03-23", "btc": 44, "price": 61763},
        {"date": "2026-04-13", "btc": 37, "price": 60892},
        {"date": "2026-04-20", "btc": 12, "price": 62570},
        {"date": "2026-04-27", "btc": 6, "price": 66951},
        {"date": "2026-05-18", "btc": 192, "price": 67866},
        {"date": "2026-06-01", "btc": 4, "price": 64989},
        {"date": "2026-08-03", "btc": 1, "price": 56061},
        {"date": "2026-08-17", "btc": 5, "price": 55882},
        {"date": "2026-09-07", "btc": 376, "price": 67182},
        {"date": "2026-09-14", "btc": 4, "price": 67010},
        {"date": "2026-09-28", "btc": 13, "price": 74364},
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
        {"date": "2025-09-20", "type": "Capital increase", "detail": "Private placement at 1.55€/share (58.1 M€)", "montant": 58.1},
        {"date": "2026-05-11", "type": "Capital increase", "detail": "International institutional investors incl. Adam Back and TOBAM (0.66€/ABSA)", "montant": 15.2},
        {"date": "2026-08-28", "type": "Capital increase", "detail": "International institutional investors incl. Adam Back and TOBAM (0.58€/ABSA)", "montant": 21.0},
        {"date": "2026-09-02", "type": "Capital increase", "detail": "Adam Back strategic investor (0.58€/ABSA), same terms as 28 Aug 2026 operation", "montant": 7.6},
    ]

    capital_data = {
        "labels": [
            "Blockstream Capital Partners",
            "Public & Institutionnel",
            "Adam Back",
            "Dirigeants",
            "TOBAM",
            "UTXO Management"
        ],
        "values": [
            71_805_804,
            205_657_804,
            67_485_900,
            21_219_800,
            12_092_254,
            4_244_478
        ]
    }

    # ---------- Données live (endpoint "chart" uniquement, pas de .info) ----------
    btc = yf.Ticker("BTC-EUR")
    altbg = yf.Ticker("ALCPB.PA")

    btc_price, btc_price_yesterday, _ = _last_two_closes(btc)
    altbg_price, altbg_price_yesterday, yday_dt = _last_two_closes(altbg)

    if not btc_price:
        raise ValueError("Cours du BTC indisponible (Yahoo)")
    if not altbg_price:
        raise ValueError("Cours de l'action ALCPB indisponible (Yahoo)")

    # ---------- Nombre d'actions ----------
    shares_series = _shares_series(altbg)

    if SHARES_OUTSTANDING_MANUAL:
        shares_now_out = float(SHARES_OUTSTANDING_MANUAL)
        shares_yesterday = shares_now_out
    else:
        shares_now_out = float(shares_series.iloc[-1]) if shares_series is not None else None
        shares_yesterday = None
        if shares_series is not None and yday_dt is not None:
            before = shares_series[shares_series.index.date <= yday_dt.date()]
            if len(before) > 0:
                shares_yesterday = float(before.iloc[-1])
        if shares_yesterday is None:
            shares_yesterday = shares_now_out

    # ---------- Valorisation ----------
    debt_btc = debt_btc_amount * btc_price
    debt = debt_btc + debt_fiat

    btc_nav = btc_price * btc_held
    market_cap = shares_now_out * altbg_price if shares_now_out else None
    market_cap_fully_diluted = shares_fully_diluted * altbg_price

    enterprise_value = market_cap + debt if market_cap is not None else None
    enterprise_value_fully_diluted = market_cap_fully_diluted + debt

    mnav = enterprise_value / btc_nav if (enterprise_value is not None and btc_nav) else None
    mnav_diluted = enterprise_value_fully_diluted / btc_nav if btc_nav else None

    # ---------- Mois pour couvrir le mNAV ----------
    today = datetime.today()
    start_of_year = datetime(today.year, 1, 1)
    days_elapsed = max((today - start_of_year).days, 1)

    daily_yield_ytd_based = (1 + btc_yield_ytd / 100) ** (1 / days_elapsed) - 1
    days_to_cover_ytd_based = _days_to_cover(mnav, daily_yield_ytd_based)
    months_to_cover_ytd_based = days_to_cover_ytd_based / 30 if days_to_cover_ytd_based is not None else None

    daily_yield_q2_based = (1 + q2_yield / 100) ** (1 / 90) - 1
    days_to_cover_q2_based = _days_to_cover(mnav, daily_yield_q2_based)
    months_to_cover_q2_based = days_to_cover_q2_based / 30 if days_to_cover_q2_based is not None else None

    # ---------- Vitesse d'accumulation ----------
    start_date = datetime.strptime("2024-11-05", "%Y-%m-%d")
    days_since_start = (today - start_date).days
    btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

    # ---------- PCV ----------
    pcv = (mnav - 1) / months_to_cover_q2_based if (mnav is not None and months_to_cover_q2_based) else None

    # ---------- Variations sur 1 jour ----------
    btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None
    altbg_price_change_pct = ((altbg_price - altbg_price_yesterday) / altbg_price_yesterday * 100) if altbg_price_yesterday else None

    market_cap_yesterday = (shares_yesterday * altbg_price_yesterday) if (shares_yesterday and altbg_price_yesterday) else None
    btc_nav_yesterday = (btc_price_yesterday * btc_held) if btc_price_yesterday else None
    enterprise_value_yesterday = (market_cap_yesterday + debt) if market_cap_yesterday is not None else None
    mnav_yesterday = (enterprise_value_yesterday / btc_nav_yesterday) if (enterprise_value_yesterday and btc_nav_yesterday) else None
    mnav_change_pct = ((mnav - mnav_yesterday) / mnav_yesterday * 100) if (mnav and mnav_yesterday) else None

    # ---------- Par action ----------
    btc_per_share = btc_held / shares_now_out if shares_now_out else None
    satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None
    btc_value_per_share_eur = btc_per_share * btc_price if btc_per_share is not None else None

    # ---------- Investi / gain ----------
    invest_price = sum(entry["btc"] * entry["price"] for entry in btc_history)
    btc_gain = btc_nav - invest_price
    btc_torque = btc_nav / invest_price if invest_price else None

    return {
        "btc_held": btc_held,
        "debt": debt,
        "debt_btc": debt_btc,
        "debt_fiat": debt_fiat,
        "enterprise_value": enterprise_value,
        "btc_yield_ytd": btc_yield_ytd,
        "q2_yield": q2_yield,
        "btc_price": round(btc_price, 2),
        "btc_per_day": _round(btc_per_day, 3),
        "share_price": round(altbg_price, 2),
        "btc_nav": round(btc_nav, 2),
        "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
        "market_cap": _round(market_cap, 2),
        "mnav_diluted": _round(mnav_diluted, 3),
        "mnav": _round(mnav, 3),
        "days_to_cover_q2_based": _round(days_to_cover_q2_based, 2),
        "pcv": _round(pcv, 3),
        "months_to_cover_q2_based": _round(months_to_cover_q2_based, 2),
        "btc_price_change_pct": _round(btc_price_change_pct, 2),
        "share_price_change_pct": _round(altbg_price_change_pct, 2),
        "mnav_change_pct": _round(mnav_change_pct, 2),
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
    }


def get_metrics():
    now = time.time()

    # Réponse en cache encore fraîche
    if _cache["data"] is not None and now - _cache["ts"] < CACHE_TTL_SECONDS:
        return jsonify(_cache["data"])

    try:
        data = _compute_metrics()
        _cache["data"] = data
        _cache["ts"] = now
        return jsonify(data)
    except Exception as e:
        # Yahoo en panne : on sert la dernière valeur valide plutôt qu'une erreur
        if _cache["data"] is not None:
            stale = dict(_cache["data"])
            stale["stale"] = True
            return jsonify(stale)
        return jsonify({"error": str(e)}), 500


def get_altbg_metrics():
    return get_metrics()
