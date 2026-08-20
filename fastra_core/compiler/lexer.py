
"""
Stage 1: Lexer - Validasi CCM JSON/envelope.
"""
from typing import Dict, Any, List, Optional, Optional
import json
from fastra_core.compiler.ccm_envelope import CCMEnvelope

class Lexer:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def load(self, source) -> Optional[CCMEnvelope]:
        """source: dict atau JSON string."""
        if isinstance(source, str):
            try:
                data = json.loads(source)
            except json.JSONDecodeError as e:
                self.errors.append({"error_code": "LEX-001", "message": str(e)})
                return None
        else:
            data = source
        if not isinstance(data, dict):
            self.errors.append({"error_code": "LEX-001", "message": "Root must be object"})
            return None
        env = CCMEnvelope(
            ccm_version=data.get("ccm_version", ""),
            project_uuid=data.get("project_uuid", ""),
            entities=data.get("entities", []),
            relationships=data.get("relationships", []),
        )
        self.errors.extend(env.validate())
        return env if not self.errors else None
