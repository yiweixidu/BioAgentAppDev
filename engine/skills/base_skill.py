# engine/skills/base_skill.py
"""
Abstract base for all BioAgent skills.
IP contract: every skill declares owner = 'platform'|'lab'|'shared'
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SkillResult:
    skill_id:      str
    input_type:    str
    summary:       str
    full_output:   dict  = field(default_factory=dict)
    confidence:    float = 0.0
    provenance:    list  = field(default_factory=list)
    model_version: str   = ""
    ip_owner:      str   = "platform"
    timestamp:     str   = field(default_factory=lambda:
                               datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    error:         str   = ""

    def to_display_text(self) -> str:
        if self.error:
            return f"[ERROR] {self.error}"
        lines = [f"{self.skill_id}  ·  {self.input_type}", "─" * 44, self.summary]
        if self.provenance:
            lines += ["", "Provenance:  " + "  ·  ".join(self.provenance)]
        lines += ["", f"Confidence: {self.confidence:.2f}   IP: {self.ip_owner}   Model: {self.model_version}"]
        return "\n".join(lines)

    def to_summary_line(self) -> str:
        return f"ERROR: {self.error[:80]}" if self.error else self.summary[:120]


class BaseSkill(ABC):

    @property
    @abstractmethod
    def skill_id(self) -> str: ...

    @property
    @abstractmethod
    def owner(self) -> str: ...

    @property
    @abstractmethod
    def input_type(self) -> str: ...

    @abstractmethod
    def validate_input(self, input_text: str) -> tuple: ...

    @abstractmethod
    def _execute(self, input_text: str, context: dict) -> dict: ...

    def run(self, input_text: str, context: dict = None) -> SkillResult:
        """Public entry point. Never raises — wraps errors in SkillResult."""
        context = context or {}
        valid, reason = self.validate_input(input_text)
        if not valid:
            return SkillResult(skill_id=self.skill_id, input_type=self.input_type,
                               summary="", ip_owner=self.owner,
                               error=f"Invalid input: {reason}")
        try:
            r = self._execute(input_text, context)
            return SkillResult(
                skill_id=self.skill_id, input_type=self.input_type,
                summary=r.get("summary", ""), full_output=r,
                confidence=r.get("confidence", 0.0),
                provenance=r.get("provenance", []),
                model_version=r.get("model_version", self.skill_id),
                ip_owner=self._resolve_ip(context),
            )
        except Exception as e:
            return SkillResult(skill_id=self.skill_id, input_type=self.input_type,
                               summary="", ip_owner=self.owner, error=str(e))

    def _resolve_ip(self, context: dict) -> str:
        for entry in context.get("model_stack", []):
            if entry.get("skill_id") == self.skill_id:
                return entry.get("owner", self.owner)
        return self.owner

    def get_manifest(self) -> dict:
        return {"skill_id": self.skill_id, "input_type": self.input_type, "owner": self.owner}
