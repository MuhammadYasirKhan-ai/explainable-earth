"""Entry point: `streamlit run streamlit_app.py` (works without installing the package)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from explainable_earth.app import main  # noqa: E402

main()
