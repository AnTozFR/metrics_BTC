from flask import Flask
from flask_cors import CORS
from metrics_ALTBG import get_altbg_metrics
from metrics_MTPLF import get_mtplf_metrics  # Assure-toi que celle-ci existe aussi

app = Flask(__name__)
CORS(app)

@app.route("/altbg")
def altbg():
    return get_altbg_metrics()

@app.route("/mtplf")
def mtplf():
    return get_mtplf_metrics()

if __name__ == '__main__':
    app.run(debug=True)
