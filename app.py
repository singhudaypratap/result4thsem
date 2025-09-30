from flask import Flask, request, jsonify, render_template
import os, json, re

app = Flask(__name__, template_folder='templates')
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ------------------ Subject Mappings ------------------

AI_DS_SUBJECTS = {
    "4AID2-01": "Discrete Mathematics Structure",
    "4AID1-03": "Managerial Economics and Financial Accounting",
    "4AID1-02": "Technical Communication",
    "4AID3-04": "Microprocessor & Interfaces",
    "4AID4-05": "Database Management System",
    "4AID4-06": "Theory of Computation",
    "4AID4-07": "Data Communication and Computer Networks",
    "4AID4-21": "Microprocessor & Interfaces Lab",
    "4AID4-22": "Database Management System Lab",
    "4AID4-23": "Network Programming Lab",
    "4AID4-24": "Linux Shell Programming Lab",
    "4AID4-25": "Java Lab",
    "FECxx": "Foundation Courses"
}

CSAI_SUBJECTS = {
    "4CAI2-01": "Discrete Mathematics Structure",
    "4CAI1-03": "Managerial Economics and Financial Accounting",
    "4CAI1-02": "Technical Communication",
    "4CAI3-04": "Microprocessor & Interfaces",
    "4CAI4-05": "Database Management System",
    "4CAI4-06": "Theory of Computation",
    "4CAI4-07": "Data Communication and Computer Networks",
    "4CAI4-21": "Microprocessor & Interfaces Lab",
    "4CAI4-22": "Database Management System Lab",
    "4CAI4-23": "Network Programming Lab",
    "4CAI4-24": "Linux Shell Programming Lab",
    "4CAI4-25": "Java Lab",
    "FECxx": "Foundation Courses"
}

CSDS_SUBJECTS = {
    "4CDS2-01": "Discrete Mathematics Structure",
    "4CDS1-03": "Managerial Economics and Financial Accounting",
    "4CDS1-02": "Technical Communication",
    "4CDS3-04": "Microprocessor & Interfaces",
    "4CDS4-05": "Database Management System",
    "4CDS4-06": "Theory of Computation",
    "4CDS4-07": "Data Communication and Computer Networks",
    "4CDS4-21": "Microprocessor & Interfaces Lab",
    "4CDS4-22": "Database Management System Lab",
    "4CDS4-23": "Network Programming Lab",
    "4CDS4-24": "Linux Shell Programming Lab",
    "4CDS4-25": "Java Lab",
    "FECxx": "Foundation Course"
}

CS_SUBJECTS = {
    "4CS2-01": "Discrete Mathematics Structure",
    "4CS1-03": "Managerial Economics and Financial Accounting",
    "4CS1-02": "Technical Communication",
    "4CS3-04": "Microprocessor & Interfaces",
    "4CS4-05": "Database Management System",
    "4CS4-06": "Theory of Computation",
    "4CS4-07": "Data Communication and Computer Networks",
    "4CS4-21": "Microprocessor & Interfaces Lab",
    "4CS4-22": "Database Management System Lab",
    "4CS4-23": "Network Programming Lab",
    "4CS4-24": "Linux Shell Programming Lab",
    "4CS4-25": "Java Lab",
    "FEC13": "Environmental Studies"
}

CSR_SUBJECTS = {
    "4CSR2-01": "Discrete Mathematics Structure",
    "4CSR1-03": "Managerial Economics and Financial Accounting",
    "4CSR1-02": "Technical Communication",
    "4CSR3-04": "Microprocessor & Interfaces",
    "4CSR4-05": "Database Management System",
    "4CSR4-06": "Theory of Computation",
    "4CSR4-07": "Data Communication and Computer Networks",
    "4CSR4-21": "Microprocessor & Interfaces Lab",
    "4CSR4-22": "Database Management System Lab",
    "4CSR4-23": "Network Programming Lab",
    "4CSR4-24": "Linux Shell Programming Lab",
    "4CSR4-25": "Java Lab",
    "FECxx": "Foundation Courses"
}

CSIOT_SUBJECTS = {
    "4CIT2-01": "Discrete Mathematics Structure",
    "4CIT1-03": "Managerial Economics and Financial Accounting",
    "4CIT1-02": "Technical Communication",
    "4CIT3-04": "Microprocessor & Interfaces",
    "4CIT4-05": "Database Management System",
    "4CIT4-06": "Theory of Computation",
    "4CIT4-07": "Data Communication and Computer Networks",
    "4CIT4-21": "Microprocessor & Interfaces Lab",
    "4CIT4-22": "Database Management System Lab",
    "4CIT4-23": "Network Programming Lab",
    "4CIT4-24": "Linux Shell Programming Lab",
    "4CIT4-25": "Java Lab",
    "4CIT8-00": "Foundation Courses"
}

SUBJECT_MAPS = {
    "AI&DS-E": AI_DS_SUBJECTS,
    "CS(AI)-F": CSAI_SUBJECTS,
    "CS(DS)-G": CSDS_SUBJECTS,
    "CS": CS_SUBJECTS,
    "CSR-D": CSR_SUBJECTS,
    "CS(IOT)-H": CSIOT_SUBJECTS
}

ALLOWED_BRANCHES = list(SUBJECT_MAPS.keys())

# ------------------ Data Cleaning ------------------

def clean_row(row, branch):
    """Keep only limited columns and enrich subject codes with names."""
    mapping = SUBJECT_MAPS.get(branch, {})
    cleaned = {}
    r = {str(k).strip(): (v if v is not None else '') for k, v in row.items()}

    # core fields
    for key in ["Reg. No", "Name", "Uni-Roll No", "Col Roll No", "Total Back", "Result", "SGPA"]:
        for k in r.keys():
            if k.lower().replace(" ", "").replace(".", "") == key.lower().replace(" ", "").replace(".", ""):
                cleaned[key] = r[k]
                break

    # subjects (skip .1 numeric columns)
    for k, v in r.items():
        if k.endswith(".1"): 
            continue
        if k in mapping:
            cleaned[f"{mapping[k]} ({k})"] = v
        elif re.match(r'^[0-9A-Za-z]', k) and k not in cleaned:
            if k not in ["Reg", "Reg. No", "Name", "Uni-Roll No", "Col Roll No", "Total Back", "Result", "SGPA"]:
                cleaned[k] = v

    return cleaned

# ------------------ Routes ------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/result")
def result():
    reg = request.args.get("reg", "").strip()
    branch = request.args.get("branch", "").strip()
    if not reg or not branch:
        return jsonify({"error": "Registration number and branch are required"}), 400
    if branch not in ALLOWED_BRANCHES:
        return jsonify({"error": "Incorrect entries or branch selection. Please try again."}), 400

    data_file = os.path.join(DATA_DIR, f"{branch}.json")
    if not os.path.exists(data_file):
        return jsonify({"error": f"Data file for branch {branch} not found"}), 500

    try:
        with open(data_file, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception as e:
        return jsonify({"error": "Failed to read data file", "detail": str(e)}), 500

    reg_norm = reg.lower()
    matches = []
    for r in rows:
        cleaned = clean_row(r, branch)
        if cleaned.get("Reg. No", "").strip().lower() == reg_norm:
            matches.append(cleaned)

    return jsonify({"result": matches})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
