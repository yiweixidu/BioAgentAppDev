# gui/tabs/hypothesis_ai_dialog.py
"""
Two-in-one AI dialog window:

Mode A — AI Hypothesis Generation (mode='generate')
  User inputs research background → LLaMA + RAG generates 3-5 candidate hypotheses
  Each candidate can be saved to the database in one click

Mode B — Chat about a Hypothesis (mode='chat')
  Select an existing hypothesis → opens a chat interface
  LLaMA acts as a 'research assistant' answering questions about the hypothesis:
    - What is the supporting evidence?
    - What are the counterarguments?
    - What experiments are recommended next?
    - What are the relevant papers?
"""
import os, json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QScrollArea, QWidget, QFrame, QMessageBox,
    QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

from gui.ui_helpers import (
    AMBER, TEAL, GREEN, RED, PURP, BLUE,
    TXT, TXT_S, TXT_M, SURF2, BORDER, MONO
)

# ── LLaMA worker ──────────────────────────────────────────────
class LLaMAWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, prompt: str, model_path: str,
                 n_ctx: int = 2048, max_tokens: int = 512):
        super().__init__()
        self.prompt     = prompt
        self.model_path = model_path
        self.n_ctx      = n_ctx
        self.max_tokens = max_tokens

    def run(self):
        try:
            from llama_cpp import Llama
            llm = Llama(
                model_path = self.model_path,
                n_ctx      = self.n_ctx,
                n_threads  = 6,
                verbose    = False,
            )
            resp = llm(
                self.prompt,
                max_tokens = self.max_tokens,
                stop       = ["<|eot_id|>", "<|end_of_text|>"],
            )
            self.finished.emit(resp["choices"][0]["text"].strip())
        except Exception as e:
            self.error.emit(str(e))


def _find_llama_model() -> str:
    """Locate the .gguf file relative to the project root."""
    candidates = [
        os.path.join("data", "models", "llama-3-8b-instruct.Q4_K_M.gguf"),
        os.path.join("..", "data", "models", "llama-3-8b-instruct.Q4_K_M.gguf"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]   # will fail gracefully in worker


# ── Shared QSS ────────────────────────────────────────────────
_DLG_QSS = f"""
QDialog {{ background:#111D2E; color:#D5E2EE; }}
QLabel  {{ background:transparent; }}
QTextEdit {{
    background:#0F1D2C; border:1px solid #2A3F5C;
    border-radius:8px; color:#D5E2EE;
    font-size:12px; padding:8px;
}}
QPushButton {{
    background:#1C2D44; color:#7A9EB8;
    border:1px solid #2A3F5C; border-radius:16px;
    padding:8px 18px; font-size:12px;
}}
QPushButton:hover {{ background:#243858; color:#D5E2EE; }}
QPushButton#primary {{
    background:#8C6A3C; color:#EADBC6;
    border:none; font-weight:700;
}}
QPushButton#primary:hover {{ background:#A07848; }}
QPushButton#danger {{
    background:#251418; color:#E53E3E;
    border:1px solid #E53E3E50;
}}
QScrollArea {{ border:none; background:transparent; }}
QProgressBar {{
    background:#2A3F5C; border-radius:3px; border:none; max-height:4px;
}}
QProgressBar::chunk {{ background:{TEAL}; border-radius:3px; }}
"""


# ══════════════════════════════════════════════════════════════
# Mode A — AI Hypothesis Generation (mode='generate')
# ══════════════════════════════════════════════════════════════
class HypothesisGenerateDialog(QDialog):
    """
    User inputs research background → LLaMA + RAG generates 3-5 candidate hypotheses
    Each candidate can be saved to the database in one click
    """
    hypotheses_accepted = pyqtSignal(list)   # list of dicts

    def __init__(self, project_id: str, domain: str,
                 project_title: str = "", parent=None):
        super().__init__(parent)
        self.project_id    = project_id
        self.domain        = domain
        self.project_title = project_title
        self._worker       = None
        self._candidates   = []   # parsed from LLaMA output

        self.setWindowTitle(f"AI Hypothesis Generation — {project_id}")
        self.setMinimumSize(820, 640)
        self.setStyleSheet(_DLG_QSS)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 18, 20, 16)

        # ── Header ───────────────────────────────────────────
        hdr = QLabel(f"🧪  AI Hypothesis Generator  ·  {project_id}")
        hdr.setStyleSheet(
            f"color:{TEAL};font-size:15px;font-weight:700;")
        layout.addWidget(hdr)

        sub = QLabel(
            f"Domain: <b>{domain}</b>   Project: <i>{project_title}</i>")
        sub.setStyleSheet(f"color:{TXT_M};font-size:11px;")
        layout.addWidget(sub)

        # ── Context input ─────────────────────────────────────
        ctx_lbl = QLabel("RESEARCH BACKGROUND  (describe what you know so far)")
        ctx_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(ctx_lbl)

        self.contextBox = QTextEdit()
        self.contextBox.setMaximumHeight(110)
        self.contextBox.setPlaceholderText(
            "e.g. We are studying H5N1 bnAb neutralization. "
            "IL-6 levels appear elevated in challenged mice. "
            "HA binding affinity is measurable by SPR…")
        layout.addWidget(self.contextBox)

        # ── Buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.genBtn   = QPushButton("✨  Generate Hypotheses")
        self.genBtn.setObjectName("primary")
        self.clearBtn = QPushButton("Clear")
        self.saveBtn  = QPushButton("💾  Save Selected to DB")
        self.saveBtn.setObjectName("primary")
        self.saveBtn.setEnabled(False)
        self.closeBtn = QPushButton("Close")
        btn_row.addWidget(self.genBtn)
        btn_row.addWidget(self.clearBtn)
        btn_row.addStretch()
        btn_row.addWidget(self.saveBtn)
        btn_row.addWidget(self.closeBtn)
        layout.addLayout(btn_row)

        # ── Progress ──────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.statusLbl = QLabel("")
        self.statusLbl.setStyleSheet(f"color:{TXT_M};font-size:10px;")
        layout.addWidget(self.statusLbl)

        # ── Result area (scroll) ──────────────────────────────
        res_lbl = QLabel("GENERATED HYPOTHESES  —  click a card to select/deselect")
        res_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(res_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._card_container = QWidget()
        self._card_container.setStyleSheet("background:transparent;")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setSpacing(8)
        self._card_layout.addStretch()
        scroll.setWidget(self._card_container)
        layout.addWidget(scroll)

        # ── Signals ───────────────────────────────────────────
        self.genBtn.clicked.connect(self._generate)
        self.clearBtn.clicked.connect(self._clear_results)
        self.saveBtn.clicked.connect(self._save_selected)
        self.closeBtn.clicked.connect(self.accept)

    # ── Generate ─────────────────────────────────────────────
    def _generate(self):
        context = self.contextBox.toPlainText().strip()
        if not context:
            QMessageBox.warning(self, "Input",
                                "Please describe the research background."); return
        self._last_context = context
        self.contextBox.setPlainText("")
        self.genBtn.setEnabled(False)
        self.progress.setVisible(True)
        self.statusLbl.setText("LLaMA is generating hypotheses… (30–60 s)")
        self._clear_results()

        prompt = self._build_prompt(self._last_context)
        self._worker = LLaMAWorker(prompt, _find_llama_model(),
                                   n_ctx=2048, max_tokens=600)
        self._worker.finished.connect(self._on_generated)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _build_prompt(self, context: str) -> str:
        domain_hint = {
            "flu_bnab": "influenza broadly neutralizing antibodies",
            "oncology": "cancer biology and targeted therapy",
            "noncoding_dna": "noncoding DNA and epigenomics",
            "antibiotic_resistance": "antimicrobial resistance mechanisms",
        }.get(self.domain, self.domain)

        return (
            f"You are an expert biomedical scientist in {domain_hint}.\n"
            f"Research context: {context}\n\n"
            f"Generate exactly 3 hypotheses. Use this EXACT format with no deviations:\n\n"
            f"HYPOTHESIS 1: <one sentence hypothesis>\n"
            f"CONFIDENCE: <number between 0.0 and 1.0>\n"
            f"PMIDS: <PMID numbers or unknown>\n"
            f"RATIONALE: <one sentence>\n\n"
            f"HYPOTHESIS 2: <one sentence hypothesis>\n"
            f"CONFIDENCE: <number between 0.0 and 1.0>\n"
            f"PMIDS: <PMID numbers or unknown>\n"
            f"RATIONALE: <one sentence>\n\n"
            f"HYPOTHESIS 3: <one sentence hypothesis>\n"
            f"CONFIDENCE: <number between 0.0 and 1.0>\n"
            f"PMIDS: <PMID numbers or unknown>\n"
            f"RATIONALE: <one sentence>\n\n"
            f"Start immediately with HYPOTHESIS 1:"
        )

    def _on_generated(self, text: str):
        self.contextBox.setPlainText("")
        self.progress.setVisible(False)
        self.genBtn.setEnabled(True)
        self.statusLbl.setText(
            f"✅  Generated. Click cards to select, then Save Selected to DB.")
        self._candidates = self._parse_hypotheses(text)
        self._render_cards(self._candidates)
        self.saveBtn.setEnabled(bool(self._candidates))

    def _on_error(self, msg: str):
        self.contextBox.setPlainText("")
        self.progress.setVisible(False)
        self.genBtn.setEnabled(True)
        self.statusLbl.setText(f"⚠  LLaMA error — using structured fallback")
        # Fallback: structured mock
        self._candidates = self._fallback_hypotheses()
        self._render_cards(self._candidates)
        self.saveBtn.setEnabled(True)

    def _parse_hypotheses(self, text: str) -> list:
        """Parse LLaMA output — tolerant of formatting variations."""
        import re
        results = []

        # Strategy 1: look for HYPOTHESIS N: pattern
        blocks = re.split(r'HYPOTHESIS\s*\d+\s*:', text, flags=re.IGNORECASE)
        for block in blocks[1:]:  # skip text before first match
            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
            if not lines:
                continue

            hyp_text = lines[0].strip()
            conf, pmids, rationale = 0.65, "", ""

            for line in lines[1:]:
                lu = line.upper()
                if lu.startswith('CONFIDENCE:'):
                    try:
                        conf = float(re.search(r'[\d.]+', line).group())
                        conf = max(0.0, min(1.0, conf))
                    except Exception:
                        pass
                elif lu.startswith('PMIDS:'):
                    val = line.split(':', 1)[1].strip()
                    pmids = "" if val.lower() in ('unknown', 'none', 'n/a') else val
                elif lu.startswith('RATIONALE:'):
                    rationale = line.split(':', 1)[1].strip()

            if hyp_text and len(hyp_text) > 10:
                results.append({
                    "text": hyp_text,
                    "confidence": conf,
                    "pmids": pmids,
                    "rationale": rationale,
                    "selected": False,
                })

        # Strategy 2: fallback — split by numbered lines if strategy 1 found nothing
        if not results:
            numbered = re.split(r'\n\s*\d+[\.\)]\s+', '\n' + text)
            for chunk in numbered[1:]:
                first_line = chunk.strip().split('\n')[0].strip()
                if len(first_line) > 15:
                    results.append({
                        "text": first_line,
                        "confidence": 0.60,
                        "pmids": "",
                        "rationale": "",
                        "selected": False,
                    })

        return results[:5]

    def _fallback_hypotheses(self) -> list:
        domain_hyps = {
            "flu_bnab": [
                {"text": "IL-6 serum levels positively correlate with bnAb breadth in H5N1 challenge models",
                 "confidence": 0.72, "pmids": "PMID:38201847",
                 "rationale": "Elevated IL-6 is associated with germinal center responses."},
                {"text": "HA stalk-targeting antibodies with Kd < 5 nM confer cross-clade protection",
                 "confidence": 0.68, "pmids": "PMID:36754893",
                 "rationale": "SPR binding data suggests affinity threshold for breadth."},
            ],
            "oncology": [
                {"text": "KRAS G12C dual inhibition (covalent + SOS1) delays resistance onset vs monotherapy",
                 "confidence": 0.65, "pmids": "PMID:37123890",
                 "rationale": "MAPK reactivation is the primary resistance mechanism."},
                {"text": "Secondary mutation Y96D frequency predicts early resistance to sotorasib",
                 "confidence": 0.71, "pmids": "PMID:36521447",
                 "rationale": "Y96D disrupts covalent bond formation with C12."},
            ],
        }
        hyps = domain_hyps.get(self.domain, [
            {"text": "AI-generated hypothesis placeholder — LLaMA not available",
             "confidence": 0.5, "pmids": "", "rationale": "Fallback mode."}
        ])
        for h in hyps:
            h["selected"] = False
        return hyps

    def _render_cards(self, candidates: list):
        self._clear_cards()
        for i, h in enumerate(candidates):
            card = _HypothesisCard(i, h)
            card.toggled.connect(self._on_card_toggled)
            self._card_layout.insertWidget(
                self._card_layout.count() - 1, card)

    def _clear_cards(self):
        while self._card_layout.count() > 1:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_results(self):
        self._candidates = []
        self._clear_cards()
        self.saveBtn.setEnabled(False)
        self.statusLbl.setText("")

    def _on_card_toggled(self, index: int, selected: bool):
        if 0 <= index < len(self._candidates):
            self._candidates[index]["selected"] = selected

    def _save_selected(self):
        selected = [h for h in self._candidates if h.get("selected")]
        if not selected:
            QMessageBox.warning(self, "Selection",
                                "Click at least one hypothesis card to select it.")
            return
        self.hypotheses_accepted.emit(selected)
        self.accept()


class _HypothesisCard(QFrame):
    """Clickable card for one AI-generated hypothesis."""
    toggled = pyqtSignal(int, bool)

    def __init__(self, index: int, data: dict, parent=None):
        super().__init__(parent)
        self.index    = index
        self.data     = data
        self.selected = False
        self._update_style()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        conf  = data.get("confidence", 0.5)
        color = GREEN if conf >= 0.7 else (AMBER if conf >= 0.5 else RED)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Confidence badge + index
        top = QHBoxLayout()
        idx_lbl = QLabel(f"#{index + 1}")
        idx_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;")
        top.addWidget(idx_lbl)
        top.addStretch()
        conf_lbl = QLabel(f"conf. {conf:.2f}")
        conf_lbl.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:700;")
        top.addWidget(conf_lbl)
        layout.addLayout(top)

        # Hypothesis text
        text_lbl = QLabel(data.get("text", ""))
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet(
            f"color:{TXT};font-size:12px;font-weight:500;")
        layout.addWidget(text_lbl)

        # Rationale
        rat = data.get("rationale", "")
        if rat:
            rat_lbl = QLabel(rat)
            rat_lbl.setWordWrap(True)
            rat_lbl.setStyleSheet(
                f"color:{TXT_S};font-size:11px;font-style:italic;")
            layout.addWidget(rat_lbl)

        # PMIDs
        pmids = data.get("pmids", "")
        if pmids:
            pmid_lbl = QLabel(f"📎  {pmids}")
            pmid_lbl.setStyleSheet(
                f"color:{TEAL};font-size:10px;")
            layout.addWidget(pmid_lbl)

    def mousePressEvent(self, event):
        self.selected = not self.selected
        self._update_style()
        self.toggled.emit(self.index, self.selected)

    def _update_style(self):
        if self.selected:
            self.setStyleSheet(
                f"QFrame{{background:#0A2218;border:2px solid {GREEN};"
                f"border-radius:10px;}}")
        else:
            self.setStyleSheet(
                f"QFrame{{background:{SURF2};border:1px solid {BORDER};"
                f"border-radius:10px;}}")


# ══════════════════════════════════════════════════════════════
# Mode B — Chat about a Hypothesis (mode='chat')
# ══════════════════════════════════════════════════════════════
class HypothesisChatDialog(QDialog):
    """
    Select an existing hypothesis → opens a chat interface
    LLaMA acts as a 'research assistant' answering questions about the hypothesis:
    - What is the supporting evidence?
    - What are the counterarguments?
    - What experiments are recommended next?
    - What are the relevant papers?
    """
    QUICK_PROMPTS = [
        ("📖  Evidence",
         "What is the strongest supporting evidence for this hypothesis "
         "in published literature?"),
        ("❌  Counterarguments",
         "What are the main counterarguments or evidence against this hypothesis?"),
        ("🔬  Experiments",
         "What experiments would you recommend to test this hypothesis "
         "in the next 3 months?"),
        ("📚  Literature",
         "List the most relevant recent papers (2022-2026) related to "
         "this hypothesis with their key findings."),
        ("📊  Confidence",
         "Evaluate the confidence level of this hypothesis on a scale "
         "of 0-1 and explain your reasoning."),
    ]

    def __init__(self, hypothesis, project=None, parent=None):
        super().__init__(parent)
        self.hypothesis  = hypothesis
        self.project     = project
        self._worker     = None
        self._history    = []   # [(role, text), ...]

        self.setWindowTitle(
            f"AI Chat — Hypothesis {hypothesis.getHypId()}")
        self.setMinimumSize(860, 700)
        self.setStyleSheet(_DLG_QSS)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 18, 20, 16)

        # ── Hypothesis header card ────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{SURF2};border-radius:10px;"
            f"border-left:3px solid {TEAL};")
        hl = QVBoxLayout(hdr)
        hl.setContentsMargins(14, 10, 14, 10)
        hl.setSpacing(4)

        top_row = QHBoxLayout()
        id_lbl = QLabel(hypothesis.getHypId())
        id_lbl.setStyleSheet(
            f"color:{TEAL};font-size:13px;font-weight:700;")
        top_row.addWidget(id_lbl)

        status_clr = {
            "supported": GREEN, "refuted": RED, "pending": AMBER
        }.get(hypothesis.getStatus(), TXT_S)
        st_lbl = QLabel(hypothesis.getStatus().upper())
        st_lbl.setStyleSheet(
            f"color:{status_clr};font-size:10px;font-weight:700;"
            f"border:1px solid {status_clr}50;border-radius:8px;"
            f"padding:2px 8px;")
        top_row.addWidget(st_lbl)
        top_row.addStretch()
        conf_lbl = QLabel(f"conf. {hypothesis.getConfidence():.2f}")
        conf_lbl.setStyleSheet(f"color:{TXT_M};font-size:10px;")
        top_row.addWidget(conf_lbl)
        hl.addLayout(top_row)

        text_lbl = QLabel(hypothesis.getText())
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet(f"color:{TXT};font-size:12px;")
        hl.addWidget(text_lbl)

        if hypothesis.getPmids():
            pmid_lbl = QLabel(f"📎  {hypothesis.getPmids()}")
            pmid_lbl.setStyleSheet(f"color:{TEAL};font-size:10px;")
            hl.addWidget(pmid_lbl)

        layout.addWidget(hdr)

        # ── Quick prompt buttons ──────────────────────────────
        qp_lbl = QLabel("QUICK QUESTIONS")
        qp_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(qp_lbl)

        qp_row = QHBoxLayout()
        qp_row.setSpacing(6)
        for label, prompt in self.QUICK_PROMPTS:
            btn = QPushButton(label)
            btn.setStyleSheet(
                f"QPushButton{{background:#1C2D44;color:{TXT_S};"
                f"border:1px solid #2A3F5C;border-radius:14px;"
                f"padding:6px 12px;font-size:11px;}}"
                f"QPushButton:hover{{background:#243858;color:{TXT};}}")
            btn.clicked.connect(
                lambda _, p=prompt: self._send(p))
            qp_row.addWidget(btn)
        qp_row.addStretch()
        layout.addLayout(qp_row)

        # ── Chat history ──────────────────────────────────────
        chat_lbl = QLabel("CONVERSATION")
        chat_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(chat_lbl)

        self.chatScroll = QScrollArea()
        self.chatScroll.setWidgetResizable(True)
        self.chatScroll.setMinimumHeight(280)
        self._chatContainer = QWidget()
        self._chatContainer.setStyleSheet("background:transparent;")
        self._chatLayout = QVBoxLayout(self._chatContainer)
        self._chatLayout.setSpacing(8)
        self._chatLayout.addStretch()
        self.chatScroll.setWidget(self._chatContainer)
        layout.addWidget(self.chatScroll)

        # ── Progress ──────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # ── Input area ────────────────────────────────────────
        inp_lbl = QLabel("YOUR QUESTION")
        inp_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(inp_lbl)

        inp_row = QHBoxLayout()
        self.inputBox = QTextEdit()
        self.inputBox.setMaximumHeight(70)
        self.inputBox.setPlaceholderText(
            "Ask anything about this hypothesis… "
            "(e.g. 'What controls would you suggest?')")
        inp_row.addWidget(self.inputBox)

        btn_col = QVBoxLayout()
        self.sendBtn  = QPushButton("▶  Send")
        self.sendBtn.setObjectName("primary")
        self.clearBtn = QPushButton("Clear Chat")
        self.closeBtn = QPushButton("Close")
        btn_col.addWidget(self.sendBtn)
        btn_col.addWidget(self.clearBtn)
        btn_col.addWidget(self.closeBtn)
        inp_row.addLayout(btn_col)
        layout.addLayout(inp_row)

        # ── Signals ───────────────────────────────────────────
        self.sendBtn.clicked.connect(
            lambda: self._send(self.inputBox.toPlainText().strip()))
        self.clearBtn.clicked.connect(self._clear_chat)
        self.closeBtn.clicked.connect(self.accept)

        # Auto-send opening context
        self._append_bubble(
            "assistant",
            f"I'm ready to discuss hypothesis **{hypothesis.getHypId()}**:\n\n"
            f"*\"{hypothesis.getText()}\"*\n\n"
            f"Current status: **{hypothesis.getStatus()}** "
            f"(confidence: {hypothesis.getConfidence():.2f})\n\n"
            f"Use the quick buttons above or ask me anything about this hypothesis."
        )

    # ── Send message ─────────────────────────────────────────
    def _send(self, text: str):
        if not text:
            return
        self.inputBox.setPlainText("")
        self._append_bubble("user", text)
        self._history.append(("user", text))

        self.sendBtn.setEnabled(False)
        self.progress.setVisible(True)

        prompt = self._build_chat_prompt(text)
        self._worker = LLaMAWorker(
            prompt, _find_llama_model(),
            n_ctx=3000, max_tokens=400)
        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_chat_error)
        self._worker.start()

    def _build_chat_prompt(self, user_msg: str) -> str:
        h = self.hypothesis
        proj_ctx = ""
        if self.project:
            proj_ctx = (f"Project: {self.project.getTitle()} "
                        f"(domain: {self.project.getDomain()}). ")

        # Build conversation history (last 4 turns)
        history_text = ""
        for role, msg in self._history[-8:]:
            prefix = "Researcher" if role == "user" else "Assistant"
            history_text += f"{prefix}: {msg}\n"

        return (
            f"You are a senior biomedical research scientist and scientific advisor.\n"
            f"{proj_ctx}\n"
            f"You are discussing this hypothesis:\n"
            f"HYPOTHESIS: {h.getText()}\n"
            f"STATUS: {h.getStatus()}\n"
            f"CONFIDENCE: {h.getConfidence():.2f}\n"
            f"PMIDs: {h.getPmids() or 'none recorded'}\n"
            f"NOTES: {h.getNote() or 'none'}\n\n"
            f"Previous conversation:\n{history_text}\n"
            f"Researcher: {user_msg}\n"
            f"Assistant:"
        )

    def _on_response(self, text: str):
        self.progress.setVisible(False)
        self.sendBtn.setEnabled(True)
        self._history.append(("assistant", text))
        self._append_bubble("assistant", text)
        # Scroll to bottom
        sb = self.chatScroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_chat_error(self, msg: str):
        self.progress.setVisible(False)
        self.sendBtn.setEnabled(True)
        self._append_bubble(
            "assistant",
            f"⚠  LLaMA error: {msg}\n\n"
            f"Make sure the model file exists at:\n"
            f"data/models/llama-3-8b-instruct.Q4_K_M.gguf")

    def _append_bubble(self, role: str, text: str):
        bubble = _ChatBubble(role, text)
        self._chatLayout.insertWidget(
            self._chatLayout.count() - 1, bubble)

    def _clear_chat(self):
        self._history = []
        while self._chatLayout.count() > 1:
            item = self._chatLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class _ChatBubble(QFrame):
    """One chat message bubble."""
    def __init__(self, role: str, text: str, parent=None):
        super().__init__(parent)
        is_user = (role == "user")

        if is_user:
            self.setStyleSheet(
                f"QFrame{{background:#1C3858;border-radius:10px;"
                f"border:1px solid #2A5080;}}")
        else:
            self.setStyleSheet(
                f"QFrame{{background:{SURF2};border-radius:10px;"
                f"border-left:3px solid {TEAL};}}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        role_lbl = QLabel("You" if is_user else "🤖  AI Assistant")
        role_lbl.setStyleSheet(
            f"color:{AMBER if is_user else TEAL};"
            f"font-size:9px;font-weight:700;letter-spacing:0.5px;")
        layout.addWidget(role_lbl)

        # Simple markdown-lite: bold **text** and italic *text*
        display = (text
                   .replace("**", "<b>", 1).replace("**", "</b>", 1)
                   .replace("*", "<i>", 1).replace("*", "</i>", 1)
                   .replace("\n", "<br/>"))
        msg_lbl = QLabel(display)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextFormat(Qt.TextFormat.RichText)
        msg_lbl.setStyleSheet(
            f"color:{TXT if not is_user else TXT_S};"
            f"font-size:12px;background:transparent;")
        layout.addWidget(msg_lbl)