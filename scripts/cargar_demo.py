"""Regenera los datos de demostracion en data/*.json.

Uso:  python scripts/cargar_demo.py [--forzar]

Sin --forzar el script se niega a sobrescribir archivos existentes, para no
borrar por accidente los datos con los que se esta probando. La logica vive en
prestamos.demo, para que se pueda verificar con pruebas.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prestamos.demo import cargar  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga los datos de demostracion")
    parser.add_argument("--forzar", action="store_true", help="sobrescribe los archivos existentes")
    cargar(parser.parse_args().forzar)
