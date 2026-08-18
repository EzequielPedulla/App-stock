import os
from pathlib import Path


def _default_db_path() -> Path:
    """Ubica la base de datos fuera de la carpeta del proyecto (que puede
    estar sincronizada con OneDrive) para evitar bloqueos o corrupción
    mientras la app escribe."""
    override = os.getenv('APP_STOCK_DB_PATH')
    if override:
        path = Path(override)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    base = os.getenv('LOCALAPPDATA') or str(Path.home())
    data_dir = Path(base) / 'App-Stock'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / 'app_stock.db'


DB_PATH = _default_db_path()
