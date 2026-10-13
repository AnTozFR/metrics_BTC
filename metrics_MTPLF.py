from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import math
import time

# ---------------------------------------------------------------------------
# Cache serveur : évite d'appeler Yahoo à chaque requête du front
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 120
_cache = {"ts": 0.0, "data": None}

# Nombre d'actions en circulation à forcer si Yahoo renvoie une valeur fausse.
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


def _shares_series(ticker, start="2024-01-01"):
    """Historique du nombre d'actions en circulation (Yahoo), nettoyé."""
    try:
        sh = ticker.get_shares_full(start=start)
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
    shares_fully_diluted = 1_631_382_824
    btc_held = 43000
    btc_yield_ytd = 9.61
    q2_yield = 4.2
    debt_btc = 0
    debt_fiat = 95_310_000_000

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
        {"date": "2025-12-30", "btc": 4279.00, "price": 16325156},
        {"date": "2026-03-31", "btc": 5075.00, "price": 12686250},
        {"date": "2026-06-30", "btc": 2823.00, "price": 12712055},
    ]

    # ---------- Données live (endpoint "chart" uniquement, pas de .info) ----------
    btc = yf.Ticker("BTC-JPY")
    mtplf = yf.Ticker("3350.T")

    btc_price, btc_price_yesterday, _ = _last_two_closes(btc)
    mtplf_price, mtplf_price_yesterday, yday_dt = _last_two_closes(mtplf)

    if not btc_price:
        raise ValueError("Cours du BTC indisponible (Yahoo)")
    if not mtplf_price:
        raise ValueError("Cours de l'action 3350.T indisponible (Yahoo)")

    # ---------- Nombre d'actions ----------
    shares_series = _shares_series(mtplf, start="2024-01-01")

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
    debt = debt_btc + debt_fiat

    btc_nav = btc_price * btc_held
    market_cap = shares_now_out * mtplf_price if shares_now_out else None
    market_cap_fully_diluted = shares_fully_diluted * mtplf_price

    enterprise_value = market_cap + debt if market_cap is not None else None
    enterprise_value_fully_diluted = market_cap_fully_diluted + debt

    mnav = enterprise_value / btc_nav if (enterprise_value is not None and btc_nav) else None
    mnav_diluted = enterprise_value_fully_diluted / btc_nav if btc_nav else None

    # ---------- Mois pour couvrir le mNAV ----------
    daily_yield_q2_based = (1 + q2_yield / 100) ** (1 / 90) - 1

    days_to_cover_q2_based = _days_to_cover(mnav, daily_yield_q2_based)
    months_to_cover_q2_based = days_to_cover_q2_based / 30 if days_to_cover_q2_based is not None else None

    days_to_cover_q2_based_diluted = _days_to_cover(mnav_diluted, daily_yield_q2_based)
    months_to_cover_q2_based_diluted = days_to_cover_q2_based_diluted / 30 if days_to_cover_q2_based_diluted is not None else None

    # ---------- Vitesse d'accumulation ----------
    # Début du programme Bitcoin de Metaplanet = premier achat de l'historique
    today = datetime.today()
    start_date = datetime.strptime("2024-04-23", "%Y-%m-%d")
    days_since_start = (today - start_date).days
    btc_per_day = btc_held / days_since_start if days_since_start > 0 else None

    # BTC Yield mensuel moyen (mois en cours inclus)
    months_elapsed = today.month
    btc_yield_monthly = btc_yield_ytd / months_elapsed if months_elapsed > 0 else None

    # ---------- PCV ----------
    pcv = (mnav - 1) / months_to_cover_q2_based if (mnav is not None and months_to_cover_q2_based) else None

    # ---------- Variations sur 1 jour ----------
    btc_price_change_pct = ((btc_price - btc_price_yesterday) / btc_price_yesterday * 100) if btc_price_yesterday else None
    mtplf_price_change_pct = ((mtplf_price - mtplf_price_yesterday) / mtplf_price_yesterday * 100) if mtplf_price_yesterday else None

    market_cap_yesterday = (shares_yesterday * mtplf_price_yesterday) if (shares_yesterday and mtplf_price_yesterday) else None
    btc_nav_yesterday = (btc_price_yesterday * btc_held) if btc_price_yesterday else None
    enterprise_value_yesterday = (market_cap_yesterday + debt) if market_cap_yesterday is not None else None
    mnav_yesterday = (enterprise_value_yesterday / btc_nav_yesterday) if (enterprise_value_yesterday and btc_nav_yesterday) else None
    mnav_change_pct = ((mnav - mnav_yesterday) / mnav_yesterday * 100) if (mnav and mnav_yesterday) else None

    # ---------- Par action ----------
    btc_per_share = btc_held / shares_now_out if shares_now_out else None
    satoshi_per_share = btc_per_share * 100_000_000 if btc_per_share is not None else None
    btc_value_per_share_jpy = btc_per_share * btc_price if btc_per_share is not None else None

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
        "share_price": round(mtplf_price, 2),
        "btc_nav": round(btc_nav, 2),
        "market_cap_fully_diluted": round(market_cap_fully_diluted, 2),
        "market_cap": _round(market_cap, 2),
        "mnav": _round(mnav, 3),
        "mnav_diluted": _round(mnav_diluted, 3),
        "pcv": _round(pcv, 3),
        "btc_yield_monthly_pct": _round(btc_yield_monthly, 2),
        "btc_price_change_pct": _round(btc_price_change_pct, 2),
        "share_price_change_pct": _round(mtplf_price_change_pct, 2),
        "mnav_change_pct": _round(mnav_change_pct, 2),
        "shares_fully_diluted": shares_fully_diluted,
        "shares_now_out": shares_now_out,
        "btc_history": btc_history,
        "btc_per_share": btc_per_share,
        "satoshi_per_share": satoshi_per_share,
        "btc_value_per_share": btc_value_per_share_jpy,
        "invest_price": round(invest_price, 2),
        "btc_gain": round(btc_gain, 2),
        "btc_torque": btc_torque,
        "months_to_cover_q2_based": _round(months_to_cover_q2_based, 2),
        "months_to_cover_q2_based_diluted": _round(months_to_cover_q2_based_diluted, 2),
    }


def get_metrics():
    now = time.time()

    if _cache["data"] is not None and now - _cache["ts"] < CACHE_TTL_SECONDS:
        return jsonify(_cache["data"])

    try:
        data = _compute_metrics()
        _cache["data"] = data
        _cache["ts"] = now
        return jsonify(data)
    except Exception as e:
        if _cache["data"] is not None:
            stale = dict(_cache["data"])
            stale["stale"] = True
            return jsonify(stale)
        return jsonify({"error": str(e)}), 500


def get_mtplf_metrics():
    return get_metrics()
