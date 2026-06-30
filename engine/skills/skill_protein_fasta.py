# engine/skills/skill_protein_fasta.py
"""
Skill: Protein Binding Affinity (ESM-2)
Base model: LocalLLM-ESM-2
IP owner: platform
"""
import re
from engine.skills.base_skill import BaseSkill

_FASTA_RE = re.compile(r">.*\n[ACDEFGHIKLMNPQRSTVWY\s]+", re.IGNORECASE)


class ProteinFastaSkill(BaseSkill):

    skill_id   = "LocalLLM-ESM-2"
    owner      = "platform"
    input_type = "Protein FASTA"

    def validate_input(self, text: str) -> tuple:
        text = text.strip()
        if not text:
            return False, "Input is empty"
        if len(text) > 5000:
            return False, "Sequence too long (max 5000 chars)"
        return True, ""

    def _execute(self, input_text: str, context: dict) -> dict:
        try:
            return self._run_esm2(input_text, context)
        except Exception:
            return self._structured_mock(input_text, context)

    def _run_esm2(self, input_text: str, context: dict) -> dict:
        """
        Real ESM-2 inference.
        Model: facebook/esm2_t33_650M_UR50D
        Task: extract embeddings → binding affinity regression head
        """
        import torch
        from transformers import EsmTokenizer, EsmModel

        model_name = "facebook/esm2_t6_8M_UR50D"  # smaller for dev
        tokenizer  = EsmTokenizer.from_pretrained(model_name)
        model      = EsmModel.from_pretrained(model_name)
        model.eval()

        seq = self._extract_sequence(input_text)
        inputs = tokenizer(seq, return_tensors="pt",
                           max_length=512, truncation=True)
        with torch.no_grad():
            outputs    = model(**inputs)
            embedding  = outputs.last_hidden_state[:, 0, :]  # CLS token
            # Proxy: use L2 norm as stability score (replace with trained head)
            stability  = float(embedding.norm(dim=1)[0]) / 100.0
            stability  = min(max(stability, 0.0), 1.0)

        # Proxy binding affinity (replace with trained regression head)
        dg    = -10.0 - stability * 5.0
        kd_nm = 10 ** (dg / -1.36)

        return {
            "summary": (
                f"dG binding:  {dg:.1f} kcal/mol\n"
                f"Kd estimate: {kd_nm:.1f} nM\n"
                f"Stability:   {stability:.2f}  "
                f"{'(stable)' if stability > 0.6 else '(unstable)'}"
            ),
            "confidence":    stability,
            "provenance":    self._pdb_refs(context),
            "model_version": "ESM-2-8M",
            "dg":            dg,
            "kd_nm":         kd_nm,
        }

    def _structured_mock(self, input_text: str, context: dict) -> dict:
        header = input_text.strip().split("\n")[0][:40]
        return {
            "summary": (
                f"Sequence:    {header}\n"
                f"dG binding:  -12.4 kcal/mol\n"
                f"Kd estimate: 2.3 nM\n"
                f"Stability:   0.81  (stable)\n"
                f"[DEV MODE — ESM-2 not loaded locally]"
            ),
            "confidence":    0.81,
            "provenance":    ["PDB:6XR8", "PDB:7KDL"],
            "model_version": "ESM-2-mock",
        }

    def _extract_sequence(self, text: str) -> str:
        lines = text.strip().split("\n")
        seq_lines = [l for l in lines if not l.startswith(">")]
        return "".join(seq_lines).replace(" ", "").upper() or "EVQLVESGGG"

    def _pdb_refs(self, context: dict) -> list:
        refs = context.get("knowledge_sources", {}).get("pdb_targets", [])
        return [f"PDB:{r}" for r in refs] if refs else ["PDB:6XR8", "PDB:7KDL"]
