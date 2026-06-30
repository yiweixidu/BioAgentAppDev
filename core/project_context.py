# core/project_context.py
"""
ProjectProfile.yaml loader and runtime context.

Each project has a YAML file at:
    manifests/profiles/{proj_id}.yaml

The context is injected into every engine skill call so skills
know which data sources, model stack, and IP rules apply.

Usage:
    ctx = ProjectContext.load("PRJ-101")
    result = skill.run(input_text, ctx.to_dict())
"""

import os
import yaml
from dataclasses import dataclass, field


PROFILES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "manifests", "profiles"
)
DEFAULT_PROFILE = os.path.join(PROFILES_DIR, "_default.yaml")


@dataclass
class ProjectContext:
    project_id:       str
    pi:               str                = ""
    domain:           str                = "general"
    model_stack:      list               = field(default_factory=list)
    knowledge_sources: dict              = field(default_factory=dict)
    fine_tuning:      dict               = field(default_factory=dict)
    hypothesis_engine: dict              = field(default_factory=dict)
    benchmarks:       dict               = field(default_factory=dict)
    grants:           list               = field(default_factory=list)
    ip_rules:         dict               = field(default_factory=dict)

    # ── Loaders ──────────────────────────────────────────────────

    @classmethod
    def load(cls, project_id: str) -> "ProjectContext":
        """
        Load profile for project_id.
        Falls back to _default.yaml if project-specific file missing.
        """
        profile_path = os.path.join(PROFILES_DIR, f"{project_id}.yaml")
        if not os.path.exists(profile_path):
            profile_path = DEFAULT_PROFILE

        with open(profile_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Allow _default.yaml to be overridden by project file
        if profile_path == DEFAULT_PROFILE:
            data["project_id"] = project_id
        else:
            data.setdefault("project_id", project_id)

        return cls(
            project_id        = data.get("project_id", project_id),
            pi                = data.get("pi", ""),
            domain            = data.get("domain", "general"),
            model_stack       = data.get("model_stack", []),
            knowledge_sources = data.get("knowledge_sources", {}),
            fine_tuning       = data.get("fine_tuning", {}),
            hypothesis_engine = data.get("hypothesis_engine", {}),
            benchmarks        = data.get("benchmarks", {}),
            grants            = data.get("grants", []),
            ip_rules          = data.get("ip_rules", {}),
        )

    # ── Helpers ──────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "project_id":        self.project_id,
            "pi":                self.pi,
            "domain":            self.domain,
            "model_stack":       self.model_stack,
            "knowledge_sources": self.knowledge_sources,
            "fine_tuning":       self.fine_tuning,
            "hypothesis_engine": self.hypothesis_engine,
            "benchmarks":        self.benchmarks,
            "grants":            self.grants,
            "ip_rules":          self.ip_rules,
        }

    def get_ip_owner(self, skill_id: str) -> str:
        """
        Return IP owner for a given skill_id based on model_stack rules.
        Falls back to 'platform' for base models.
        """
        for entry in self.model_stack:
            if entry.get("skill_id") == skill_id:
                return entry.get("owner", "platform")
        return "platform"

    def allows_private_data(self) -> bool:
        return self.knowledge_sources.get("private_lake", False)

    def pubmed_query(self) -> str:
        return self.knowledge_sources.get("pubmed_query", "")

    def rag_enabled_for_grants(self) -> bool:
        return any(g.get("rag_enabled", False) for g in self.grants)
