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
    except EOFError:
        # Ocurre cuando se cierra la entrada estandar, por ejemplo al canalizar
        # comandos o al cerrar la terminal. No es un defecto, asi que no se
        # reporta a Sentry.
        print("\nEntrada terminada. Hasta luego")
        return 0
    except Exception as fallo:
        identificador = excepcion("error_fatal", fallo)
        print(f"\nError fatal: {fallo}")
        if identificador:
            print(f"Referencia del reporte: {identificador}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
