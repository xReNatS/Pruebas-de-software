"""Permite ejecutar la aplicacion con: python -m prestamos"""

import sys

from .cli.app import ejecutar
from .registro import excepcion


def main() -> int:
    try:
        return ejecutar()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
        return 130
    except Exception as fallo:
        excepcion("error_fatal", fallo)
        print(f"\nError fatal: {fallo}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
