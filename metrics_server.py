from flask import Flask
from flask_cors import CORS
from metrics_ALTBG import get_altbg_metrics
from metrics_ALTBG_FMP import get_altbg_fmp_metrics
from metrics_MSTR import get_mstr_metrics
from metrics_MTPLF import get_mtplf_metrics
from metrics_SWC import get_swc_metrics
from metrics_h100 import get_h100_metrics

app = Flask(__name__)
CORS(app)

@app.route("/altbg")
def altbg():
    return get_altbg_metrics()

@app.route("/altbg_fmp")
def altbg_fmp():
    return get_altbg_fmp_metrics()

@app.route("/mtplf")
def mtplf():
    return get_mtplf_metrics()

@app.route("/swc")
def swc():
    return get_swc_metrics()

@app.route("/mstr")
def mstr():
    return get_mstr_metrics()

@app.route("/h100")
def h100():
    return get_h100_metrics()

if __name__ == '__main__':
    app.run(debug=True)
