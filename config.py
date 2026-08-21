import os
import sys
from pathlib import Path


def _portable_db_path() -> Path | None:
    """Si hay un app_stock.db al lado del ejecutable, se usa esa copia:
    permite llevar la app y su base juntas en un pendrive (por ejemplo
    para una demo en otra PC) sin tener que copiar nada a carpetas del
    sistema en cada máquina."""
    app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) \
        else Path(__file__).parent
    candidate = app_dir / 'app_stock.db'
    return candidate if candidate.exists() else None


def _default_db_path() -> Path:
    """Ubica la base de datos fuera de la carpeta del proyecto (que puede
    estar sincronizada con OneDrive) para evitar bloqueos o corrupción
    mientras la app escribe."""
    override = os.getenv('APP_STOCK_DB_PATH')
    if override:
        path = Path(override)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    portable = _portable_db_path()
    if portable:
        return portable

    base = os.getenv('LOCALAPPDATA') or str(Path.home())
    data_dir = Path(base) / 'App-Stock'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / 'app_stock.db'


DB_PATH = _default_db_path()
