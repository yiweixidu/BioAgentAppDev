# BioAgent — Phase 1 Technical Documentation

> Covers: Phase 1 core architecture, report export feature, local LLaMA deployment, login/logout system
> Last updated: 2026-06-30

---

## Table of Contents

1. [Phase 1 — Core Architecture](#1-phase-1--core-architecture)
2. [Report Export & Dashboard Integration](#2-report-export--dashboard-integration)
3. [Local LLaMA Deployment](#3-local-llama-deployment)
4. [Login / Logout System](#4-login--logout-system)
5. [Complete Installation Steps](#5-complete-installation-steps)
6. [Project Structure Overview](#6-project-structure-overview)

---

## 1. Phase 1 — Core Architecture

### 1.1 Design Goals

| Requirement | Implementation |
|---|---|
| L0 compliance from day one | SHA-256 audit chain + RBAC + IP registry |
| All four Agents/Skills functional | DNABERT-2 / ESM-2 / PPI / LLaMA+RAG |
| ProjectProfile.yaml | Per-project config, injected at runtime |
| SQL only | No Neo4j / ChromaDB yet — deferred to Phase 2 |
| PyQt6 | Built on the existing desktop application framework |
| IP ownership | Every inference record tagged platform / lab / shared |

### 1.2 Key Concepts Clarified

| Term | Meaning |
|---|---|
| **Base Model** (platform IP) | DNABERT-2, ESM-2, PPI, LLaMA — the foundation models you own exclusively |
| **Skill** (ModelSkill table) | A LoRA adapter fine-tuned by a lab on top of a base model; IP may be lab or shared |
| **Inference** (InferenceRecord table) | A single record of "running a task with a given Skill" |
| **Engine/Registry** | The runtime system that routes input to the correct Skill and executes it |

### 1.3 Directory Structure

```
bioagent/
├── core/
│   ├── audit_chain.py        # L0: SHA-256 chained audit log
│   ├── access_control.py     # L0: RBAC (SQL-backed)
│   └── project_context.py    # ProjectProfile.yaml loader
├── engine/
│   ├── skill_registry.py     # Unified entry point for all Skills
│   └── skills/
│       ├── base_skill.py         # Abstract base class + SkillResult
│       ├── skill_dna_variant.py  # DNABERT-2 (platform IP)
│       ├── skill_protein_fasta.py # ESM-2 (platform IP)
│       ├── skill_ppi.py          # PPI predictor (platform IP)
│       └── skill_rag.py          # LLaMA + FAISS RAG (platform IP)
├── manifests/profiles/
│   ├── _default.yaml
│   ├── PRJ-101.yaml          # flu_bnab project config
│   └── PRJ-102.yaml          # oncology project config
├── dao/                      # Data access layer (unchanged from original)
├── models/                   # Data models (unchanged from original)
├── gui/tabs/
│   └── inference_tab.py      # Rewritten: wired to real Skills + L0 audit
└── database/schema.sql       # New audit_chain / ip_registry / rbac tables
```

### 1.4 L0 Compliance — SHA-256 Audit Chain

**Core mechanism**: each audit entry's `chain_hash = SHA256(payload_hash + previous chain_hash)`. If any record is tampered with, every subsequent hash fails to match, making the audit log tamper-evident.

```python
from core.audit_chain import AuditChain

AuditChain.log(
    user_id     = "RES-001",
    action      = "INFERENCE",
    entity_type = "inference",
    entity_id   = "INF-001",
    detail      = "type=DNA Variant skill=LocalLLM-DNABERT-2",
    project_id  = "PRJ-102",
    ip_owner    = "platform",   # platform | lab | shared
)

# Verify integrity
ok, msg = AuditChain.verify_chain(limit=500)
# → (True, "OK — 3 entries verified")
```

New database tables: `audit_chain`, `rbac_role`, `rbac_permission`, `ip_registry`, `loi25_consent` (reserved for Quebec privacy law compliance).

### 1.5 ProjectProfile.yaml

Each project has its own YAML config file, injected into Skill calls at runtime to determine which models, knowledge sources, and IP ownership rules apply.

```yaml
# manifests/profiles/PRJ-101.yaml
project_id: PRJ-101
pi: Dr. Lefrançois
domain: flu_bnab

model_stack:
  - skill_id: LocalLLM-ESM-2     # platform base model
    owner: platform
  - skill_id: SK-002              # lab fine-tuned adapter
    owner: shared
    lab_share_pct: 60

knowledge_sources:
  pubmed_query: "H5N1 broadly neutralizing antibody hemagglutinin"
  pdb_targets: ["6XR8", "7KDL"]
  private_lake: true              # lab's proprietary data

grants:
  - grant_id: GR-001
    type: CIHR
    rag_enabled: true
```

If no profile exists for a given project, the system automatically falls back to `_default.yaml`.

### 1.6 The Unified Skill Contract

All Skills inherit from `BaseSkill`, must declare IP ownership, and `run()` never raises — errors are wrapped in `SkillResult.error`:

```python
class BaseSkill(ABC):
    skill_id:   str   # unique identifier
    owner:      str   # 'platform' | 'lab' | 'shared'
    input_type: str   # e.g. 'DNA Variant'

    def validate_input(self, text: str) -> tuple: ...
    def _execute(self, input_text: str, context: dict) -> dict: ...
    def run(self, input_text: str, context: dict) -> SkillResult: ...
```

| Skill | Underlying Model | IP Owner | Phase 1 Status |
|---|---|---|---|
| DNA Variant | DNABERT-2-117M | platform | ✅ Real inference |
| Protein FASTA | ESM-2 | platform | ✅ Real inference |
| PPI Antibody–Antigen | ESM-2 cosine proxy | platform | ✅ Real inference (Phase 2: upgrade to dedicated model) |
| Literature RAG | sentence-transformers + FAISS + LLaMA | platform | ✅ Real retrieval + generation |

Each Skill has three fallback layers: real model inference → structured mock (when the model isn't loaded) → unified `SkillResult` output. The UI never crashes due to a missing model.

---

## 2. Report Export & Dashboard Integration

### 2.1 New Files

| File | Purpose |
|---|---|
| `core/report_generator.py` | Generates PI-ready PDF reports using reportlab |
| `gui/tabs/inference_result_dialog.py` | Full result viewer dialog |
| `dao/dao_inference.py` (updated) | Supports `get_by_project()`, stores `result_full` JSON |

### 2.2 Three Use Cases

**Export a report**: Select a project in the Inference History table → click `📄 Export Project Report` → generates a PDF containing all inference results, source citations, hypothesis table, and grant status.

**Dashboard integration**: The Dashboard's Recent Inference Results card displays IP ownership color tags (platform = teal / lab = amber / shared = green) and confidence scores.

**Full results for the PI**: Double-click any row in Inference History → opens the full result viewer, showing input, complete output, and source citations. Individual records can be exported as PDF or copied to clipboard.

### 2.3 PDF Report Contents

```
1. Project metadata (ID / PI / Domain / Status)
2. IP ownership notice (legal statement on platform IP vs shared IP)
3. Per-inference results (input / output / provenance / confidence / IP tag)
4. Hypothesis summary table
5. Grant status table
6. L0 audit chain integrity statement
```

### 2.4 Database Changes

The `inference_history` table gained three new fields:

```sql
ALTER TABLE inference_history
ADD COLUMN result_full LONGTEXT,      -- full SkillResult.full_output as JSON
ADD COLUMN confidence  FLOAT,
ADD COLUMN ip_owner    VARCHAR(20) DEFAULT 'platform';
```

### 2.5 Installing Dependencies

```powershell
python -m pip install reportlab
```

---

## 3. Local LLaMA Deployment

### 3.1 Approach Comparison

| | Ollama | Manual .gguf (chosen approach) |
|---|---|---|
| Setup difficulty | Simple | Moderate |
| Code changes | Requires adapting the call interface | None needed |
| Control granularity | Coarser | Fine-grained (quantization level, thread count, etc.) |

The manual `.gguf` download + `llama-cpp-python` approach was adopted.

### 3.2 Setup Steps

```powershell
# 1. Install llama-cpp-python (CPU build)
python -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# 2. Create the model directory
mkdir data\models

# 3. Download the model (~4.9GB)
python -m pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='bartowski/Meta-Llama-3-8B-Instruct-GGUF', filename='Meta-Llama-3-8B-Instruct-Q4_K_M.gguf', local_dir='data/models')"

# 4. Rename to the filename expected by the codebase
Rename-Item "data\models\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf" "llama-3-8b-instruct.Q4_K_M.gguf"

# 5. Install RAG retrieval dependencies
python -m pip install sentence-transformers faiss-cpu einops
```

### 3.3 Verifying the Real Model Is Loaded

Check the `Model:` field on the last line of the Result box:

| Displayed Value | Meaning |
|---|---|
| `Model: DNABERT-2-117M` | ✅ Real model |
| `Model: DNABERT-2-mock` | ⚠️ Fallback mode |
| `Model: RAG-MiniLM-L6+FAISS` + fluent paragraph text | ✅ Real LLaMA generation |
| Numbered list-style output | ⚠️ Extractive fallback |

### 3.4 Measured Performance (CPU inference)

```
llama_perf_context_print: eval time = 11298 ms / 63 runs (179.34 ms per token, 5.58 tokens per second)
```

Roughly 5.6 tokens/second; a single RAG query takes about 30–60 seconds end-to-end (including model load time).

### 3.5 Key Implementation Detail

LLaMA 3 uses `<|eot_id|>` as its stop token rather than the default `\n\n`. The `stop` parameter must be set correctly when calling the model:

```python
llm = Llama(model_path=model_path, n_ctx=2048, n_threads=6, verbose=False)
response = llm(prompt, max_tokens=300,
               stop=["<|eot_id|>", "<|end_of_text|>"])
```

### 3.6 Phase 1 Skill Verification Summary

```
LocalLLM-DNABERT-2             OK
LocalLLM-ESM-2                 OK
LocalLLM-PPI                   OK
LocalLLM-RAG                   OK
```

Audit Chain verification: `✅ OK — 3 entries verified`

Real RAG output example:
```
Query: KRAS G12C inhibitor resistance mechanisms

Answer: KRAS G12C inhibitors, such as sotorasib, can develop resistance
through MAPK reactivation. Additionally, secondary mutations Y96D and
H95D can confer resistance to covalent KRAS G12C inhibitors...

Provenance: PMID:35039682 · PMID:37123890 · PMID:36521447
Confidence: 0.76   IP: platform   Model: RAG-MiniLM-L6+FAISS
```

---

## 4. Login / Logout System

### 4.1 Role Permission Matrix

| Role | Manage Options Visibility | Notes |
|---|---|---|
| `admin` | ✅ Visible | Super Admin |
| `pi` | ✅ Visible | Super Admin |
| `lab_manager` | ✅ Visible | Super Admin |
| `researcher` | ❌ Hidden | Standard user |
| `viewer` | ❌ Hidden | Read-only |

### 4.2 New Files

| File | Purpose |
|---|---|
| `core/session.py` | Global session singleton holding the logged-in user's info |
| `gui/login_dialog.py` | Login screen, validates email + password |
| `main.py` (rewritten) | Login ⇄ MainWindow loop |
| `main_window.py` (updated) | Top status bar + Logout button |
| `projects_tab.py` / `researcher_tab.py` (updated) | `CURRENT_USER_ROLE` replaced with `Session.can_manage_options()` |

### 4.3 Session Singleton Usage

```python
from core.session import Session

# Set after successful login (called by LoginDialog)
Session.set(res_id="RES-001", name="Dr. Liwei Rong",
            role="researcher", email="liwei@vanier.ca")

# Read from anywhere
Session.current_role()        # 'researcher'
Session.can_manage_options()  # False
Session.require_role(['admin', 'pi'])  # raises PermissionError if not satisfied
```

### 4.4 Login Validation Logic

Passwords are stored as SHA-256 hashes in `researcher.password`. Seed accounts have an empty password string, so the first login can be done with a blank password field:

```
Email:    liwei.rong@vanier.ca
Password: (leave blank)
Role:     researcher

Email:    ana.cardinal@vanier.ca
Password: (leave blank)
Role:     lab_manager
```

Setting a real password:

```sql
UPDATE researcher
SET password = SHA2('your_password', 256)
WHERE email = 'liwei.rong@vanier.ca';
```

Up to 5 failed login attempts are allowed before the application exits.

### 4.5 Audit Record on Successful Login

```python
AuditChain.log(
    user_id     = researcher["res_id"],
    action      = "LOGIN",
    entity_type = "session",
    entity_id   = researcher["res_id"],
    detail      = f"role={researcher['role']}",
    ip_owner    = "platform",
)
```

### 4.6 Logout Flow

The top status bar of the main window shows `👤 Dr. Liwei Rong [researcher]` alongside a `🚪 Logout` button. Clicking it triggers:

```
Confirmation dialog
    ↓ confirmed
Write a LOGOUT audit entry
    ↓
Session.clear()
    ↓
Emit logout_requested signal
    ↓
Close the current MainWindow
    ↓
main.py's while loop detects the logout flag → re-opens LoginDialog
```

```python
# main.py core loop logic
def run_session(app) -> bool:
    login = LoginDialog()
    if login.exec() != LoginDialog.DialogCode.Accepted:
        return False   # user cancelled → exit the program

    window = MainWindow()
    state = {"logout": False}
    window.logout_requested.connect(lambda: state.update(logout=True))
    window.show()
    app.exec()
    return state["logout"]   # True → re-login; False → exit

while True:
    if not run_session(app):
        break
```

---

## 5. Complete Installation Steps

```powershell
# ── 1. Clone/extract the project ──────────────────────
cd BioAgentAppDev

# ── 2. Install core dependencies ──────────────────────
python -m pip install PyQt6 PyMySQL PyYAML torch transformers

# ── 3. Install RAG dependencies ───────────────────────
python -m pip install sentence-transformers faiss-cpu einops

# ── 4. Install the LLaMA inference engine ─────────────
python -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# ── 5. Install report generation dependencies ─────────
python -m pip install reportlab

# ── 6. Configure the database ─────────────────────────
copy config\db_config.example.py config\db_config.py
# Edit db_config.py with your MySQL credentials

mysql -u root -p < database\schema.sql
mysql -u root -p bioagent_db < database\seed_data.sql

# ── 7. Download the LLaMA model ───────────────────────
mkdir data\models
python -m pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='bartowski/Meta-Llama-3-8B-Instruct-GGUF', filename='Meta-Llama-3-8B-Instruct-Q4_K_M.gguf', local_dir='data/models')"
Rename-Item "data\models\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf" "llama-3-8b-instruct.Q4_K_M.gguf"

# ── 8. Launch ──────────────────────────────────────────
python main.py
```

### Verification Checklist

```powershell
# Verify all four Skills are functional
python -c "
import sys; sys.path.insert(0, '.')
from engine.skill_registry import get
tests = [
    ('LocalLLM-DNABERT-2', 'chr12:25398284 A>T hg38',       {'domain':'oncology'}),
    ('LocalLLM-ESM-2',     '>Ab_VH\nEVQLVESGGG',            {'domain':'flu_bnab'}),
    ('LocalLLM-PPI',       'EVQLVESGGG\n\nMKTLLLTLVVV',     {}),
    ('LocalLLM-RAG',       'KRAS G12C resistance mechanisms',{'domain':'oncology'}),
]
for sid, inp, ctx in tests:
    r = get(sid).run(inp, ctx)
    print(f'{sid:30s} {\"ERROR: \"+r.error if r.error else \"OK\"}')"

# Verify audit chain integrity
python -c "
import sys; sys.path.insert(0, '.')
from core.audit_chain import AuditChain
print(AuditChain.verify_chain())"
```

---

## 6. Project Structure Overview

> The structure below has been verified against the actual project screenshots, including all `__init__.py` package markers.

```
BioAgentAppDev/
├── .venv/                        # Python virtual environment (library root)
├── .gitattributes
├── .gitignore
├── main.py                       # Updated: Login⇄MainWindow loop
├── requirements-core.txt         # PyQt6 / PyMySQL / PyYAML / matplotlib / reportlab
├── requirements-ai.txt           # torch / transformers / llama-cpp-python / faiss, etc.
├── requirements-dev.txt          # pytest
│
├── config/
│   ├── __init__.py
│   ├── db_config.py
│   └── db_config.example.py
│
├── core/
│   ├── __init__.py
│   ├── access_control.py         # L0: RBAC
│   ├── audit_chain.py            # L0: SHA-256 audit chain
│   ├── project_context.py        # ProjectProfile.yaml loader
│   ├── report_generator.py       # PDF report generation
│   └── session.py                # Login session singleton
│
├── dao/
│   ├── __init__.py
│   ├── dao_audit.py
│   ├── dao_grant.py
│   ├── dao_hypothesis.py
│   ├── dao_inference.py          # Updated: supports full_output storage
│   ├── dao_model_skill.py
│   ├── dao_options.py
│   ├── dao_project.py
│   ├── dao_researcher.py
│   └── db_connection.py
│
├── data/
│   ├── models/
│   │   ├── .cache/                          # huggingface-hub download cache
│   │   │   └── huggingface/
│   │   │       ├── download/
│   │   │       ├── .gitignore
│   │   │       └── CACHEDIR.TAG
│   │   └── llama-3-8b-instruct.Q4_K_M.gguf  # ~4.9GB, downloaded manually
│   └── faiss_indices/                        # Per-project FAISS indices (generated at runtime)
│
├── database/
│   ├── schema.sql                # Updated: includes L0 compliance tables
│   └── seed_data.sql
│
├── engine/
│   ├── __init__.py
│   ├── skill_registry.py
│   └── skills/
│       ├── __init__.py
│       ├── base_skill.py
│       ├── skill_dna_variant.py
│       ├── skill_protein_fasta.py
│       ├── skill_ppi.py
│       └── skill_rag.py
│
├── gui/
│   ├── __init__.py
│   ├── login_dialog.py           # New: login screen
│   ├── main_window.py            # Updated: top bar + Logout
│   ├── manage_options_dialog.py
│   ├── ui_helpers.py
│   └── tabs/
│       ├── __init__.py
│       ├── dashboard_chart_canvas.py    # New: dark-themed matplotlib canvas base class
│       ├── dashboard_chart_dialogs.py   # New: Progress/Spending chart dialogs
│       ├── dashboard_tab.py             # Updated: double-click cards open charts
│       ├── grant_tab.py
│       ├── hypothesis_ai_dialog.py      # New: AI generate/chat dialog
│       ├── hypothesis_tab.py            # Updated: AI generation + chat features
│       ├── inference_result_dialog.py   # New: full result viewer
│       ├── inference_tab.py             # Updated: real Skills + export
│       ├── knowledge_tab.py
│       ├── projects_tab.py              # Updated: Session-based permission checks
│       └── researcher_tab.py            # Updated: Session-based permission checks
│
├── manifests/
│   ├── __init__.py
│   └── profiles/
│       ├── __init__.py
│       ├── _default.yaml
│       ├── PRJ-101.yaml
│       └── PRJ-102.yaml
│
└── models/
    ├── __init__.py
    ├── audit_entry.py
    ├── grant_fund.py
    ├── hypothesis.py
    ├── inference_record.py
    ├── milestone.py
    ├── model_skill.py
    ├── project.py
    └── researcher.py
```

### Notes

- `data/models/.cache/huggingface/` is a cache directory auto-generated by `huggingface-hub` when downloading the model. It doesn't need to be created manually and should not be committed to version control (already excluded in `.gitignore`).
- `reports/` (PDF export directory) and `data/faiss_indices/` (FAISS indices) are generated on demand at runtime and may not exist in the file tree before the first run — this is expected.
- Every Python package directory (`core/`, `dao/`, `engine/`, `gui/`, `models/`, `manifests/`, and their subdirectories) requires an `__init__.py`, even if empty, or module imports will fail.

---

## Appendix: Phase 2 Backlog (Not Yet Implemented)

- Real PubMed literature ETL (replacing the RAG seed corpus)
- Dedicated PPI model (replacing the ESM-2 cosine proxy)
- Neo4j knowledge graph (cross-project hypothesis linking)
- Gradio web interface (replacing PyQt6, enabling remote multi-lab access)
- ChromaDB (replacing in-memory FAISS, supporting persistent vector indices)
- MLOps pipeline (automated LoRA adapter training / evaluation / deployment)
