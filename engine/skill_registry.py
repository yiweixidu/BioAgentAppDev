# engine/skill_registry.py
"""
Skill Registry — single source of truth for all available skills.

Base models (platform IP) are registered here at startup.
Lab-trained skills (lab/shared IP) are loaded dynamically from
the model_skill DB table + their YAML manifests.

Usage:
    from engine.skill_registry import SkillRegistry
    skill = SkillRegistry.get("LocalLLM-RAG")
    result = skill.run(input_text, context.to_dict())
"""

from engine.skills.skill_dna_variant   import DNAVariantSkill
from engine.skills.skill_protein_fasta import ProteinFastaSkill
from engine.skills.skill_ppi           import PPISkill
from engine.skills.skill_rag           import LiteratureRAGSkill

# ── Base platform skills — registered once at import time ─────────
_BASE_SKILLS = {
    s.skill_id: s for s in [
        DNAVariantSkill(),
        ProteinFastaSkill(),
        PPISkill(),
        LiteratureRAGSkill(),
    ]
}

# Runtime registry (base + lab skills loaded from DB)
_registry: dict = {}
_loaded = False


def _ensure_loaded():
    global _registry, _loaded
    if _loaded:
        return
    _registry = dict(_BASE_SKILLS)  # copy base skills

    # Load active lab/shared skills from DB
    try:
        from dao.dao_model_skill import ModelSkillDAO
        from dao.dao_project     import ProjectDAO
        dao = ModelSkillDAO()
        for skill_record in dao.get_active():
            sid = skill_record.getSkillId()
            # Lab skills wrap a base model with a LoRA adapter.
            # For Phase 1: resolve to the nearest base model + tag IP.
            base_model = _resolve_base_model(skill_record.getName())
            if base_model:
                # Create a thin wrapper that overrides skill_id and owner
                wrapper = _LabSkillWrapper(skill_record, base_model)
                _registry[sid] = wrapper
    except Exception:
        pass  # DB not available → only base skills

    _loaded = True


def _resolve_base_model(fine_tune_method_or_name: str):
    """Map a fine-tune method name to its underlying base skill."""
    mapping = {
        "DNABERT-2":    _BASE_SKILLS.get("LocalLLM-DNABERT-2"),
        "ESM-2":        _BASE_SKILLS.get("LocalLLM-ESM-2"),
        "PPI Predictor":_BASE_SKILLS.get("LocalLLM-PPI"),
        "LoRA":         _BASE_SKILLS.get("LocalLLM-DNABERT-2"),  # default
        "QLoRA":        _BASE_SKILLS.get("LocalLLM-DNABERT-2"),
    }
    return mapping.get(fine_tune_method_or_name)


class _LabSkillWrapper:
    """
    Thin wrapper around a base skill that overrides skill_id and owner
    to reflect the lab/shared IP of a fine-tuned adapter.
    """
    def __init__(self, skill_record, base_skill):
        self._record = skill_record
        self._base   = base_skill
        self.skill_id   = skill_record.getSkillId()
        self.owner      = skill_record.owner if hasattr(skill_record, 'owner') else 'lab'
        self.input_type = base_skill.input_type

    def run(self, input_text: str, context: dict = None) -> object:
        ctx = dict(context or {})
        # Inject LoRA version info into context for the base skill
        ctx["lora_version"] = self._record.getLoraVersion()
        ctx["skill_id"]     = self.skill_id
        result = self._base.run(input_text, ctx)
        result.skill_id  = self.skill_id
        result.ip_owner  = self.owner
        result.model_version = (
            f"{self._base.skill_id}/{self._record.getLoraVersion()}"
        )
        return result

    def get_manifest(self) -> dict:
        return {
            "skill_id":    self.skill_id,
            "input_type":  self.input_type,
            "owner":       self.owner,
            "base_model":  self._base.skill_id,
            "lora_version": self._record.getLoraVersion(),
        }


# ── Public API ────────────────────────────────────────────────────

def get(skill_id: str):
    """Return skill instance by ID. Returns None if not found."""
    _ensure_loaded()
    return _registry.get(skill_id)


def get_all() -> dict:
    """Return all registered skills {skill_id: skill_instance}."""
    _ensure_loaded()
    return dict(_registry)


def get_base_skills() -> list:
    """Return list of platform-owned base skill instances."""
    return list(_BASE_SKILLS.values())


def refresh():
    """Force reload of lab skills from DB (call after KnowledgeTab saves)."""
    global _loaded
    _loaded = False
    _ensure_loaded()


def list_for_ui() -> list:
    """
    Return structured list for InferenceTab model picker.
    Format: [{'label': str, 'skill_id': str, 'owner': str, 'is_base': bool}]
    """
    _ensure_loaded()
    items = []
    # Base platform models first
    for sid, skill in _BASE_SKILLS.items():
        items.append({
            "label":    f"🔬  {sid}",
            "skill_id": sid,
            "owner":    "platform",
            "is_base":  True,
        })
    # Lab/shared skills
    for sid, skill in _registry.items():
        if sid not in _BASE_SKILLS:
            items.append({
                "label":    f"🛠  {sid}  [{skill.owner}]",
                "skill_id": sid,
                "owner":    skill.owner,
                "is_base":  False,
            })
    return items
