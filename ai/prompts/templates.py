"""
Prompt template system for InfraMind AI.

Provides a lightweight, string-based template engine that supports:
- Named variable substitution via ``{variable_name}`` placeholders
- Optional sections wrapped in ``{% if variable %}...{% endif %}`` blocks
- Template composition via ``{% include template_name %}`` directives
- A central registry for loading templates by name
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Template data class
# ---------------------------------------------------------------------------


@dataclass
class PromptTemplate:
    """
    A named prompt template with variable substitution support.

    Parameters
    ----------
    name:
        Unique template identifier used for registry lookups.
    template:
        The raw template string.  Variables are referenced as ``{var_name}``.
        Multi-line templates are automatically de-dented.
    description:
        Human-readable description of the template's purpose.
    required_variables:
        Variable names that *must* be supplied at render time.
    default_variables:
        Default values for optional variables.
    """

    name: str
    template: str
    description: str = ""
    required_variables: list[str] = field(default_factory=list)
    default_variables: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalise indentation so multi-line triple-quoted strings look clean
        self.template = textwrap.dedent(self.template).strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Render the template by substituting *variables*.

        Parameters
        ----------
        variables:
            Mapping of variable name → value.  Default variables are applied
            first; *variables* override them.

        Raises
        ------
        ValueError
            If any ``required_variables`` are missing from the final mapping.
        """
        merged: Dict[str, Any] = {**self.default_variables, **(variables or {})}

        missing = [v for v in self.required_variables if v not in merged]
        if missing:
            raise ValueError(
                f"Template '{self.name}' is missing required variables: {missing}"
            )

        rendered = self._render_conditionals(self.template, merged)
        rendered = self._substitute_variables(rendered, merged)
        rendered = _collapse_blank_lines(rendered)
        return rendered.strip()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _substitute_variables(template: str, variables: Dict[str, Any]) -> str:
        """
        Replace ``{variable_name}`` placeholders with values from *variables*.

        Only substitutes ``{word}`` patterns (letter/digit/underscore identifiers)
        so that literal JSON braces such as ``{"key": "value"}`` are preserved.
        Unknown placeholders are left unchanged.
        """
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(variables[key]) if key in variables else match.group(0)

        return re.sub(r"\{([A-Za-z_]\w*)\}", replacer, template)

    @staticmethod
    def _render_conditionals(template: str, variables: Dict[str, Any]) -> str:
        """
        Process simple ``{% if var %}...{% endif %}`` blocks.

        A block is included only if *var* is truthy in *variables*.
        """
        pattern = re.compile(
            r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}",
            re.DOTALL,
        )

        def replace_block(match: re.Match[str]) -> str:
            var_name = match.group(1)
            block_content = match.group(2)
            return block_content if variables.get(var_name) else ""

        return pattern.sub(replace_block, template)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _collapse_blank_lines(text: str) -> str:
    """Replace runs of more than two consecutive blank lines with a single blank line."""
    return re.sub(r"\n{3,}", "\n\n", text)


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------


class TemplateRegistry:
    """
    Central registry for all InfraMind AI prompt templates.

    Usage::

        registry = TemplateRegistry.get_instance()
        template = registry.get("infra_analysis_base")
        rendered = template.render({"resource_type": "S3 bucket", ...})
    """

    _instance: Optional[TemplateRegistry] = None
    _templates: Dict[str, PromptTemplate]

    def __init__(self) -> None:
        self._templates = {}

    # Singleton accessor
    @classmethod
    def get_instance(cls) -> TemplateRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, template: PromptTemplate) -> None:
        """Register a template, overwriting any existing entry with the same name."""
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        """
        Retrieve a template by name.

        Raises
        ------
        KeyError
            If no template with *name* is registered.
        """
        if name not in self._templates:
            raise KeyError(f"No template named '{name}' found in registry.")
        return self._templates[name]

    def list_templates(self) -> list[str]:
        """Return a sorted list of all registered template names."""
        return sorted(self._templates.keys())

    def render(self, name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Convenience method: look up a template and render it in one call."""
        return self.get(name).render(variables)


# ---------------------------------------------------------------------------
# Built-in shared templates
# ---------------------------------------------------------------------------

_SYSTEM_CONTEXT_TEMPLATE = PromptTemplate(
    name="system_context",
    description="System-level context injected at the start of every AI conversation.",
    template="""
    You are InfraMind AI, an expert cloud infrastructure analyst specialising in
    security, compliance, and operational best practices.

    Your responsibilities:
    - Analyse infrastructure configurations for security misconfigurations
    - Identify compliance gaps across CIS, SOC 2, PCI-DSS, HIPAA, and NIST frameworks
    - Assess risk levels using industry-standard scoring methodologies
    - Provide clear, actionable, and prioritised remediation guidance
    - Communicate findings concisely for both technical engineers and business stakeholders

    Always respond in valid JSON unless explicitly asked otherwise.
    Use precise technical language and cite specific configuration attributes when relevant.
    """,
)

_JSON_FORMAT_INSTRUCTIONS = PromptTemplate(
    name="json_format_instructions",
    description="Standard JSON output format instructions appended to analysis prompts.",
    template="""
    ## Output Format

    Respond **only** with a JSON object matching this schema (no markdown fences):

    {
      "summary": "<one-paragraph executive summary>",
      "findings": [
        {
          "id": "<unique-id>",
          "resource_id": "<resource-id>",
          "title": "<short title>",
          "description": "<detailed description>",
          "severity": "critical|high|medium|low|info",
          "risk_score": {
            "base_score": <0-10>,
            "exploitability": <0-1>,
            "impact": <0-1>,
            "rationale": "<score explanation>"
          },
          "affected_attribute": "<config key>",
          "evidence": "<snippet>",
          "cve_ids": [],
          "compliance_frameworks": []
        }
      ],
      "recommendations": [
        {
          "id": "<unique-id>",
          "finding_ids": ["<finding-id>"],
          "title": "<short title>",
          "description": "<detailed guidance>",
          "priority": "immediate|high|medium|low|deferred",
          "effort": "low|medium|high|very-high",
          "steps": ["<step 1>", "<step 2>"],
          "references": ["<url>"],
          "auto_remediable": false,
          "automation_script": null
        }
      ]
    }
    """,
)

_FOCUS_AREAS_SNIPPET = PromptTemplate(
    name="focus_areas_snippet",
    description="Optional snippet listing analysis focus areas.",
    required_variables=["focus_areas"],
    template="""
    {% if focus_areas %}
    Pay particular attention to the following areas: {focus_areas}.
    {% endif %}
    """,
)

# Register built-ins
_registry = TemplateRegistry.get_instance()
for _t in [_SYSTEM_CONTEXT_TEMPLATE, _JSON_FORMAT_INSTRUCTIONS, _FOCUS_AREAS_SNIPPET]:
    _registry.register(_t)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_registry() -> TemplateRegistry:
    """Return the global template registry singleton."""
    return TemplateRegistry.get_instance()


def render_template(name: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """Render a registered template by name."""
    return get_registry().render(name, variables)
