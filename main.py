"""Punto de entrada del proyecto.

Existe para poder ejecutar la aplicacion con `python main.py` desde la raiz,
sin tener que configurar PYTHONPATH a mano en cada sistema operativo. La
alternativa `python -m prestamos` sigue funcionando si `src` esta en el path.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from prestamos.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
