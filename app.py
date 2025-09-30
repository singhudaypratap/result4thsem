"""
app.py - Flask backend for PIET result lookup

Key behavior:
- Cross-branch lookup by registration (reg parameter).
- Cleans rows and maps subject codes to full subject names using SUBJECT_MAPS.
- Skips duplicate Excel columns that end with .1, .2, ...
- Does NOT include "Col Roll No" in the response (as requested).
- Adds 'Branch' (human-friendly) showing which JSON file contained the record.
"""

from flask import Flask, jsonify, request, render_template
import os, json, re

app = Flask(__name__, template_folder='templates')

# Data directory relative to this file
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------
# Subject mapping per branch
# (code -> descriptive name)
# Fill/expand these as needed; based on your teaching scheme earlier.
# ---------------------------

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
    "FEC13": "Foundation Courses"
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
    "FEC13": "Foundation Courses"
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
    "FEC12": "Foundation Course"
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
    "FEC13": "Foundation Courses"
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
    "FEC13": "Foundation Courses"
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
    "FEC13": "Foundation Courses"
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

# ---------------------------
# Utilities
# ---------------------------

def load_rows_for_branch(branch):
    """Load the JSON list for a given branch (empty list if not found)."""
    path = os.path.join(DATA_DIR, f"{branch}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
            if isinstance(obj, list):
                return obj
            return []
    except Exception as e:
        # On file read error, return empty
        print(f"Error loading {path}: {e}")
        return []

def find_reg_values_in_row(row):
    """
    Return a list of registration-like strings found in the row values or keys.
    (Used to match user-provided reg against the row)
    """
    regs = []
    for k, v in row.items():
        # keys that look like registration fields
        if isinstance(k, str):
            kl = k.strip().lower()
            if any(s in kl for s in ("reg", "registration", "regno", "reg.no", "regno.")):
                if isinstance(v, str) and v.strip():
                    regs.append(v.strip())
        # values containing PIET
        if isinstance(v, str) and "PIET" in v.upper():
            regs.append(v.strip())
    return regs

def clean_row_map_subjects(row, branch):
    """
    Produce a cleaned dict from the raw row for JSON output:
    - Normalizes core fields to friendly keys (Reg. No, Name, Uni-Roll No, Total Back, Result, SGPA)
    - Skips 'Col Roll No'
    - Maps known subject codes to full subject names and uses keys like "Database Management System (4CS4-05)"
    - Skips duplicate columns ending with .1, .2, ...
    - Adds "Branch" key (friendly)
    """
    mapping = SUBJECT_MAPS.get(branch, {})
    cleaned = {}
    # Normalize keys to string and keep values
    r = {str(k).strip(): (v if v is not None else '') for k, v in row.items()}

    # Core fields mapping (common variations)
    core_targets = {
        "Reg. No": ["reg. no", "reg", "registration", "regno", "registration no"],
        "Name": ["name", "student name"],
        "Uni-Roll No": ["uni-roll no", "uni roll no", "uni roll", "uni-roll", "uniroll"],
        # intentionally skip 'Col Roll No' - we don't send it to frontend
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

    # Map subject-like columns (skip duplicates named like '4CS4-05.1')
    for k, v in r.items():
        if re.search(r'\.\d+$', k):
            # skip duplicate columns created during excel->json conversion
            continue
        # skip col roll explicitly
        if k.lower().replace(" ", "") in ("colrollno","colroll","colrollno."):
            continue
        # if this key is a known code for this branch map to name
        if k in mapping:
            subject_name = mapping[k]
            keyname = f"{subject_name} ({k})"
            cleaned[keyname] = v
        else:
            # If key appears subject-like (letters + digits), include it but use the key itself as fallback label.
            if re.search(r'[A-Za-z]', k) and re.search(r'\d', k):
                cleaned[k] = v

    # Friendly branch label
    cleaned["Branch"] = branch
    return cleaned

# ---------------------------
# Routes
# ---------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/result")
def result():
    """
    Query parameter:
      - reg: registration number (required)
    Optional:
      - branch: hint (we prefer this branch first if valid)
    """
    reg = request.args.get("reg", "").strip()
    branch_hint = request.args.get("branch", "").strip()

    if not reg:
        return jsonify({"error": "Registration number is required"}), 400

    reg_norm = reg.strip().lower()

    # Determine branch search order
    if branch_hint and branch_hint in ALLOWED_BRANCHES:
        branches_to_check = [branch_hint] + [b for b in ALLOWED_BRANCHES if b != branch_hint]
    else:
        branches_to_check = ALLOWED_BRANCHES[:]

    matches = []
    for b in branches_to_check:
        rows = load_rows_for_branch(b)
        for raw in rows:
            regs_in_row = find_reg_values_in_row(raw)
            regs_norm = [s.strip().lower() for s in regs_in_row if isinstance(s, str)]
            matched = False
            for cand in regs_norm:
                # exact equality or flexible prefix matching
                if cand == reg_norm or cand.startswith(reg_norm) or reg_norm.startswith(cand):
                    cleaned = clean_row_map_subjects(raw, b)
                    matches.append(cleaned)
                    matched = True
                    break
            if matched:
                # continue scanning current branch to find other duplicates if any
                continue
        if matches:
            # stop after the first branch that contained the reg (to prefer branch order)
            break

    return jsonify({"result": matches})

@app.route("/api/branches")
def branches():
    """Return which branch JSONs exist (useful for frontend debugging)."""
    info = {}
    for b in ALLOWED_BRANCHES:
        info[b] = {"exists": os.path.exists(os.path.join(DATA_DIR, f"{b}.json"))}
    return jsonify(info)

# ---------------------------
# Run (for development)
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
