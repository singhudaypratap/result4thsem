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

# ------------------ Utilities & Cleaning ------------------

def find_reg_values_in_row(row):
    """Return possible registration-like strings from a raw row dict."""
    regs = []
    for k, v in row.items():
        if not isinstance(k, str):
            continue
        kl = k.strip().lower()
        # keys that look like registration fields
        if any(s in kl for s in ("reg", "registration", "regno", "reg.no", "regno.")):
            if isinstance(v, str) and v.strip():
                regs.append(v.strip())
        # also any PIET-like token in values
        if isinstance(v, str) and "PIET" in v.upper():
            regs.append(v.strip())
    return regs

def clean_row(row, branch):
    """
    Keep only limited columns and enrich subject codes with names.
    Returns a dict with keys:
     - Reg. No, Name, Uni-Roll No, Col Roll No, [Subject Name (Code)]: grade, Total Back, Result, SGPA
    """
    mapping = SUBJECT_MAPS.get(branch, {})
    cleaned = {}
    r = {str(k).strip(): (v if v is not None else '') for k, v in row.items()}

    # core fields (normalize possibilities)
    core_targets = {
        "Reg. No": ["reg. no", "reg", "registration", "regno", "registration no"],
        "Name": ["name", "student name"],
        "Uni-Roll No": ["uni-roll no", "uni roll no", "uni roll", "uni-roll", "uniroll"],
        "Col Roll No": ["col roll no", "college roll", "col roll", "colroll", "col roll no"],
        "Total Back": ["total back", "totalback", "back", "backlog"],
        "Result": ["result", "status"],
        "SGPA": ["sgpa", "gpa", "cgpa"]
    }

    lk = {k.lower(): k for k in r.keys()}
    for dest, cand_list in core_targets.items():
        for cand in cand_list:
            for key_lower, key_orig in lk.items():
                if key_lower.replace(".", "").replace(" ", "") == cand.replace(".", "").replace(" ", ""):
                    cleaned[dest] = r.get(key_orig, "")
                    break
            if dest in cleaned:
                break

    # subjects: avoid numeric duplicate columns (end with .1, .2 etc)
    for k, v in r.items():
        if re.search(r'\.\d+$', k):  # skip duplicate numeric columns
            continue
        # if key is an exact code in mapping, use mapping
        if k in mapping:
            name = mapping[k]
            cleaned[f"{name} ({k})"] = v
        else:
            # some keys might already be full names or codes like "4CS2-01"
            # consider keys that look subject-like: contain letters+digits or common code tokens
            if re.search(r'[A-Za-z]', k) and re.search(r'\d', k):
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

    # load helper
    def load_rows_for_branch(b):
        p = os.path.join(DATA_DIR, f"{b}.json")
        if not os.path.exists(p):
            return []
        try:
            with open(p, "r", encoding="utf-8") as fh:
                obj = json.load(fh)
                if isinstance(obj, list):
                    return obj
                return []
        except Exception:
            return []

    reg_norm = reg.strip().lower()
    matches = []
    # order: try chosen branch first, then all others
    checked_branches = [branch] + [b for b in ALLOWED_BRANCHES if b != branch]

    for b in checked_branches:
        rows = load_rows_for_branch(b)
        for raw in rows:
            # get possible reg-like values from raw row
            regs_in_row = find_reg_values_in_row(raw)
            regs_in_row_norm = [s.strip().lower() for s in regs_in_row if isinstance(s, str)]
            # direct match or prefix match (to allow short/long forms)
            matched = False
            for cand in regs_in_row_norm:
                if cand == reg_norm or cand.startswith(reg_norm) or reg_norm.startswith(cand):
                    cleaned = clean_row(raw, b)
                    # annotate real branch where record was found
                    cleaned["__branch__"] = b
                    matches.append(cleaned)
                    matched = True
                    break
            if matched:
                # if found in this branch, we continue scanning this branch to collect duplicates (rare)
                continue
        if matches:
            # if found in chosen branch or in some other branch, break after first branch that contains the reg
            break

    return jsonify({"result": matches})

# ------------------ optional: small health endpoint ------------------
@app.route("/api/branches")
def branches():
    """Return allowed branches and whether their JSON exists (useful for frontend to fetch samples)"""
    info = {}
    for b in ALLOWED_BRANCHES:
        path = os.path.join(DATA_DIR, f"{b}.json")
        info[b] = {"exists": os.path.exists(path)}
    return jsonify(info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
