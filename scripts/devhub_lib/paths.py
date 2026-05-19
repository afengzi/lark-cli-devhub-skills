from __future__ import annotations

import os
from pathlib import Path


HOME = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
DEVHUB_HOME = Path(os.environ.get("DEVHUB_HOME", str(HOME / ".codex" / "devhub"))).expanduser()
CONFIG_PATH = Path(os.environ.get("DEVHUB_CONFIG", str(DEVHUB_HOME / "config.json"))).expanduser()
DEFAULT_REPO = Path(os.environ.get("DEVHUB_REPO", str(Path.cwd()))).expanduser()
