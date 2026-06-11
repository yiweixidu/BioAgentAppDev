# mock_data.py – shared data store
from datetime import datetime
from typing import List, Dict, Any

researchers: List[Dict] = [
    {"id":"RES-001","name":"Dr. Liwei Rong","institution":"Vanier College",
     "pi":"Dr. Lefrançois","domain":"flu_bnab","role":"researcher","email":"liwei.rong@vanier.ca"},
    {"id":"RES-002","name":"Dr. Ana Cardinal","institution":"Vanier College",
     "pi":"Dr. Lefrançois","domain":"noncoding_dna","role":"lab_manager","email":"ana.cardinal@vanier.ca"},
]

projects: List[Dict] = [
    {"id":"PRJ-101","title":"H5N1 bnAb Broad neutralization","domain":"flu_bnab",
     "grant":"CIHR","pi":"Dr. Lefrançois","status":"active","skill":"ESM-2","progress":75},
    {"id":"PRJ-102","title":"KRAS G12C Resistance","domain":"oncology",
     "grant":"NSERC","pi":"Dr. Liwei Rong","status":"active","skill":"DNABERT-2","progress":48},
    {"id":"PRJ-103","title":"Noncoding DNA CRISPR Screening","domain":"noncoding_dna",
     "grant":"MITACS","pi":"Dr. Ana Cardinal","status":"planning","skill":None,"progress":90},
]

hypotheses: List[Dict] = [
    {"id":"H3","project_id":"PRJ-101",
     "text":"IL-6 correlates with bnAb breadth in H5N1 challenge",
     "status":"supported","confidence":0.87,"pmids":"PMID:38201847","note":"Confirmed ELISA 2026-05-14"},
    {"id":"H14","project_id":"PRJ-102",
     "text":"KRAS G12C dual inhibition improves PFS",
     "status":"refuted","confidence":0.32,"pmids":"PMID:36521447","note":"IC50 unchanged in SPR assay"},
    {"id":"H21","project_id":"PRJ-103",
     "text":"Noncoding CpG methylation silences interferon-β",
     "status":"pending","confidence":0.65,"pmids":"PMID:37123890","note":"Awaiting second replicate"},
]

model_skills: List[Dict] = [
    {"id":"SK-001","name":"DNABERT-2","project_id":"PRJ-102",
     "lora_version":"oncology-somatic-v2","threshold":200,
     "benchmark":"BRCA_eval","status":"active","loaded":"2026-05-01"},
    {"id":"SK-002","name":"ESM-2","project_id":"PRJ-101",
     "lora_version":"flu-ha-v3","threshold":150,
     "benchmark":"HA_binding_eval","status":"active","loaded":"2026-05-01"},
    {"id":"SK-003","name":"PPI Predictor","project_id":"PRJ-101",
     "lora_version":"ppi-base-v1","threshold":100,
     "benchmark":"Antibody_PPI_eval","status":"inactive","loaded":"2026-04-20"},
]

inference_history: List[Dict] = [
    {"id":"INF-001","type":"DNA Variant","input":"chr12:25398284 A>T hg38",
     "model":"DNABERT-2","project_id":"PRJ-102",
     "result_summary":"score −1.83 · pathogenic · PMID:38201847","timestamp":"2026-05-14 10:23"},
    {"id":"INF-002","type":"Protein FASTA","input":">Ab_VH EVQLVESGGG…",
     "model":"ESM-2","project_id":"PRJ-101",
     "result_summary":"ΔG=−12.4 kcal/mol · Kd=2.3 nM · PDB:6XR8","timestamp":"2026-05-14 14:15"},
]

grants: List[Dict] = [
    {"id":"GR-001","project_id":"PRJ-101","agency":"CIHR",
     "deadline":"2026-08-30","total":120000,"used":42000,"milestone_pct":35},
    {"id":"GR-002","project_id":"PRJ-102","agency":"NSERC",
     "deadline":"2026-07-15","total":85000,"used":25500,"milestone_pct":62},
]

milestones: List[Dict] = [
    {"grant_id":"GR-001","desc":"Hemagglutinin ELISA optimization","due":"2026-06-01","completed":False},
    {"grant_id":"GR-002","desc":"CRISPR library design","due":"2026-05-10","completed":False},
]

audit_trail: List[Dict] = [
    {"timestamp":"2026-05-14 09:12","user":"Dr. Liwei Rong",
     "action":"CREATE","entity":"Project PRJ-101","detail":"New project registered"},
    {"timestamp":"2026-05-14 10:01","user":"Dr. Lefrançois",
     "action":"ASSIGN_SKILL","entity":"SK-002 → PRJ-101","detail":"ESM-2 flu-ha-v3 activated"},
    {"timestamp":"2026-05-14 14:32","user":"Dr. Liwei Rong",
     "action":"UPDATE","entity":"Hypothesis H14",
     "detail":"PENDING → REFUTED (IC50 unchanged in SPR assay)"},
]

EVALBUS = {
    "DNABERT-2":    {"pearson_r":0.74,"AUC":0.89,"vs_baseline":"+0.03"},
    "ESM-2":        {"pearson_r":0.81,"AUC":0.93,"vs_baseline":"+0.05"},
    "PPI Predictor":{"pearson_r":0.68,"AUC":0.86,"vs_baseline":"+0.05"},
}

def add_audit(user,action,entity,detail):
    audit_trail.append({"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "user":user,"action":action,"entity":entity,"detail":detail})

def get_hypothesis_counts():
    c={"supported":0,"refuted":0,"pending":0}
    for h in hypotheses:
        if h["status"] in c: c[h["status"]]+=1
    return c

def get_active_skill():
    a=next((s for s in model_skills if s["status"]=="active"),None)
    return f"{a['name']} · {a['lora_version']}" if a else "—"

def get_project_title(pid):
    return next((p["title"] for p in projects if p["id"]==pid), pid)

def next_id(lst, prefix):
    nums=[int(x["id"].split("-")[1]) for x in lst if x["id"].startswith(prefix+"-")]
    return f"{prefix}-{max(nums,default=0)+1:03d}"
