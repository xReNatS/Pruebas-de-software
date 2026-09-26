"""Hash de contrasenas.

Se usa PBKDF2-HMAC-SHA256 de la libreria estandar: nunca se guarda la
contrasena en texto plano en los archivos JSON. El formato almacenado es
pbkdf2_sha256$<iteraciones>$<sal_hex>$<hash_hex>.
"""

import hashlib
import hmac
import secrets

_ALGORITMO = "pbkdf2_sha256"
_ITERACIONES = 120_000


def hashear(contrasena: str) -> str:
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, _ITERACIONES)
    return f"{_ALGORITMO}${_ITERACIONES}${sal.hex()}${derivada.hex()}"


def verificar(contrasena: str, almacenada: str) -> bool:
    """Compara en tiempo constante. Devuelve False ante un hash mal formado."""
    try:
        algoritmo, iteraciones, sal_hex, hash_hex = almacenada.split("$")
        if algoritmo != _ALGORITMO:
            return False
        derivada = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones)
        )
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(derivada.hex(), hash_hex)
