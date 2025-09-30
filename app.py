from flask import Flask, request, jsonify, render_template
import os, json

app = Flask(__name__, template_folder='templates')

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/result")
def result():
    reg = request.args.get("reg", "").strip()
    branch = request.args.get("branch", "").strip()
    if not reg or not branch:
        return jsonify({"error": "Registration number and branch are required"}), 400
    safe_branch = branch.replace('/', '').replace('..', '')
    data_file = os.path.join(DATA_DIR, f"{safe_branch}.json")
    if not os.path.exists(data_file):
        return jsonify({"error":"Incorrect entries or branch selection. Please try again."}), 400
    try:
        with open(data_file, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception as e:
        return jsonify({"error": "Failed to read data file", "detail": str(e)}), 500
    reg_norm = reg.lower()
    matches = []
    for r in rows:
        r = {str(k): (v if v is not None else "") for k, v in r.items()}
        if any(isinstance(v, str) and v.strip().lower() == reg_norm for v in r.values()):
            matches.append(r)
    return jsonify({"result": matches})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
