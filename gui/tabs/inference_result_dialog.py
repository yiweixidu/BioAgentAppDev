# gui/tabs/inference_result_dialog.py
"""
Full Result Viewer Dialog — PI可以在这里看完整推理结果并导出PDF。
从 InferenceTab 的历史表格双击行触发。
"""
import json, os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from gui.ui_helpers import AMBER, TEAL, GREEN, RED, TXT, TXT_S, TXT_M, SURF2, BORDER

IP_COLOR = {"platform": TEAL, "lab": AMBER, "shared": GREEN}


class InferenceResultDialog(QDialog):
    """
    Shows full inference result for one record.
    Opened by double-clicking a row in the history table.
    """
    def __init__(self, record, project=None, parent=None):
        super().__init__(parent)
        self.record  = record
        self.project = project
        self.setWindowTitle(f"Inference Result — {record.getInfId()}")
        self.setMinimumSize(760, 560)
        self.setStyleSheet(f"""
            QDialog {{ background: #111D2E; color: #D5E2EE; }}
            QLabel  {{ background: transparent; }}
            QPushButton {{
                background: #1C2D44; color: #7A9EB8;
                border: 1px solid #2A3F5C; border-radius: 16px;
                padding: 8px 20px; font-size: 12px;
            }}
            QPushButton:hover {{ background: #243858; color: #D5E2EE; }}
            QPushButton#primary {{
                background: #8C6A3C; color: #EADBC6;
                border: none; font-weight: 700;
            }}
            QPushButton#primary:hover {{ background: #A07848; }}
        """)

        ip    = getattr(record, 'ip_owner', 'platform')
        conf  = getattr(record, 'confidence', None)
        color = IP_COLOR.get(ip, TEAL)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 16)

        # ── Header ───────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{SURF2};border-radius:10px;border:1px solid {color}50;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 12, 14, 12)

        id_lbl = QLabel(record.getInfId())
        id_lbl.setStyleSheet(
            f"color:{color};font-size:16px;font-weight:700;")
        hl.addWidget(id_lbl)

        for text, clr in [
            (record.getType(),  TXT),
            (record.getModel(), TXT_S),
            (f"IP: {ip.upper()}", color),
            (f"conf. {float(conf):.2f}" if conf else "", TXT_M),
        ]:
            if text:
                lbl = QLabel(text)
                lbl.setStyleSheet(
                    f"color:{clr};font-size:11px;margin-left:12px;")
                hl.addWidget(lbl)
        hl.addStretch()
        ts_lbl = QLabel(str(record.getTimestamp()))
        ts_lbl.setStyleSheet(f"color:{TXT_M};font-size:10px;")
        hl.addWidget(ts_lbl)
        layout.addWidget(hdr)

        # ── Input ─────────────────────────────────────────────
        inp_lbl = QLabel("INPUT")
        inp_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(inp_lbl)

        inp_box = QTextEdit()
        inp_box.setReadOnly(True)
        inp_box.setMaximumHeight(60)
        inp_box.setPlainText(record.getInput() or "")
        inp_box.setStyleSheet(
            f"background:#0F1D2C;border:1px solid #2A3F5C;"
            f"border-radius:6px;color:#8AAEC6;"
            f"font-family:'Cascadia Code','Consolas',monospace;font-size:11px;")
        layout.addWidget(inp_box)

        # ── Full Result ───────────────────────────────────────
        res_lbl = QLabel("FULL RESULT")
        res_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        layout.addWidget(res_lbl)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setStyleSheet(
            f"background:#0F1D2C;border:1px solid #2A3F5C;"
            f"border-left:3px solid {color};"
            f"border-radius:8px;color:#8AAEC6;"
            f"font-family:'Cascadia Code','Consolas',monospace;font-size:12px;")

        # Build full display text
        full_text = self._build_full_text(record)
        self.result_box.setPlainText(full_text)
        layout.addWidget(self.result_box)

        # ── Buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.export_pdf_btn = QPushButton("📄  Export PDF Report")
        self.export_pdf_btn.setObjectName("primary")
        self.copy_btn       = QPushButton("📋  Copy to Clipboard")
        self.close_btn      = QPushButton("Close")

        self.export_pdf_btn.clicked.connect(self._export_pdf)
        self.copy_btn.clicked.connect(self._copy)
        self.close_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.export_pdf_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def _build_full_text(self, record) -> str:
        lines = [
            f"{record.getInfId()}  ·  {record.getType()}  ·  {record.getModel()}",
            f"IP: {getattr(record,'ip_owner','platform').upper()}   "
            f"Project: {record.getProjectId() or '—'}   "
            f"Time: {record.getTimestamp()}",
            "─" * 56,
            "",
            "RESULT SUMMARY",
            record.getResultSummary() or "—",
            "",
        ]
        # Add full JSON output if available
        full_raw = getattr(record, 'result_full', '')
        if full_raw:
            try:
                full = json.loads(full_raw)
                prov = full.get("provenance", [])
                if prov:
                    lines += ["PROVENANCE", "  ·  ".join(prov), ""]
                conf = full.get("confidence")
                if conf is not None:
                    lines.append(f"Confidence: {float(conf):.3f}")
                mv = full.get("model_version")
                if mv:
                    lines.append(f"Model version: {mv}")
            except Exception:
                pass
        return "\n".join(lines)

    def _export_pdf(self):
        """Export this single record as a PDF report."""
        default_name = f"BioAgent_{self.record.getInfId()}_Report.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", default_name,
            "PDF Files (*.pdf)")
        if not path:
            return
        try:
            from core.report_generator import ReportGenerator
            out = ReportGenerator.generate_project_report(
                project_id  = self.record.getProjectId() or "UNKNOWN",
                records     = [self.record],
                project     = self.project,
                output_dir  = os.path.dirname(path),
            )
            # Rename to user-chosen path
            if out != path:
                import shutil
                shutil.move(out, path)
            QMessageBox.information(
                self, "Exported",
                f"PDF saved to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    def _copy(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.result_box.toPlainText())
        self.copy_btn.setText("✅  Copied!")
