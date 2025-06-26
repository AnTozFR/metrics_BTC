from flask import Flask, jsonify
from flask_cors import CORS
from metrics_ALTBG import get_altbg_metrics
from metrics_MTPLF import get_mtplf_metrics

app = Flask(__name__)
CORS(app)

@app.route("/altbg")
def altbg():
    return jsonify(get_altbg_metrics())

@app.route("/mtplf")
def mtplf():
    return jsonify(get_mtplf_metrics())
