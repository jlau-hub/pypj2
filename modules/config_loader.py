import logging
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
_cfg = None


def load_config() -> dict:
    global _cfg
    if _cfg is None:
        with open(ROOT / "config.yaml", encoding="utf-8") as f:
            _cfg = yaml.safe_load(f)
        for key, val in _cfg["paths"].items():
            _cfg["paths"][key] = str(ROOT / val)
    return _cfg


def setup_logging():
    cfg = load_config()
    log_dir = Path(cfg["paths"]["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
