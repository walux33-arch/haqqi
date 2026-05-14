"""Module registry for specialized legal modules.

كل وحدة (module) عندها:
- name: اسم الوحدة
- label: الاسم المعروض
- description: وصف
- match(question) -> bool: واش السؤال كيتعلق بالوحدة
- process(question, context) -> str: الجواب المخصص
"""

from typing import Optional

_registry = {}


def register(module):
    _registry[module.name] = module
    return module


def get_module(name: str) -> Optional[object]:
    return _registry.get(name)


def match_modules(question: str) -> list[object]:
    """Find all modules that match a question."""
    results = []
    for name, module in _registry.items():
        if hasattr(module, "match") and module.match(question):
            results.append(module)
    return results


def list_modules() -> list[dict]:
    return [
        {"name": m.name, "label": m.label, "description": m.description}
        for m in _registry.values()
    ]


# Import and register all modules
from app.agent.modules import admin_simplification
