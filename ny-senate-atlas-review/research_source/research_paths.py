"""Path configuration for the copied research scripts; never points at app files by default."""
from pathlib import Path
from datetime import datetime, timezone
import os
PACKAGE_ROOT = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("SENATE_RESEARCH_ROOT", PACKAGE_ROOT / "work")).expanduser().resolve()
RETRIEVED_AT = datetime.now(timezone.utc).isoformat()
for relative in ("v5_data/census/raw", "v5_data/issues", "v5_data/handoff/raw", "v5_data/handoff/charts", "election_research", "finance_research/raw", "dossier_research", "geography", "senate_v5/dist"):
    (ROOT / relative).mkdir(parents=True, exist_ok=True)
