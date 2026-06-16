"""SreToolkitPlugin: hermes-sre-toolkit para hermes-agent."""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("hermes-sre-toolkit")


class SreToolkitPlugin:
    """Plugin standalone."""
    name = "hermes-sre-toolkit"
    kind = "standalone"
    version = "1.0.0"

    def register(self, ctx) -> None:
        """Hook de registro."""
        # Tools
        ctx.register_tool("hermes_sre_toolkit_status", self._tool_status)

        # Skills
        skill_path = self._skill_path()
        if skill_path.exists():
            ctx.register_skill("hermes-sre-toolkit", skill_path)

        log.info("hermes-sre-toolkit v%s registrado", self.version)

    def _skill_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "skills" / "sre-toolkit"

    def _tool_status(self, **_):
        return {"status": "ready", "version": self.version}
