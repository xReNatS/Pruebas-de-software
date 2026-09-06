"""Regenera los datos de demostracion en data/*.json.

Uso:  python scripts/cargar_demo.py [--forzar]

Sin --forzar el script se niega a sobrescribir archivos existentes, para no
borrar por accidente los datos con los que se esta probando. Las contrasenas
de demostracion son publicas a proposito y estan documentadas en el README;
no son secretos y no deben reutilizarse fuera de este ejercicio.
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prestamos import almacen, estados, modelos, reglas  # noqa: E402

CLAVE_ENCARGADO = "labadmin2026"
CLAVE_SOLICITANTE = "demo12345"

HOY = date.today()


def _encargados() -> list[dict]:
    return [
        modelos.nuevo_encargado("ENC-0001", "Camila Rojas", "camila.rojas@lab.cl", CLAVE_ENCARGADO),
        modelos.nuevo_encargado("ENC-0002", "Diego Fuentes", "diego.fuentes@lab.cl", CLAVE_ENCARGADO),
    ]


def _solicitantes() -> list[dict]:
    personas = [
        ("Ana Perez", "12345678-5", "ana.perez@alumnos.cl"),
        ("Bruno Silva", "17890123-0", "bruno.silva@alumnos.cl"),
        ("Carla Munoz", "9876543-3", "carla.munoz@profes.cl"),
        ("Diana Torres", "20111222-2", "diana.torres@alumnos.cl"),
    ]
    registros = [modelos.nuevo_solicitante(n, r, c, CLAVE_SOLICITANTE) for n, r, c in personas]
    # Diana arrastra un atraso: sirve para probar que no puede pedir equipos.
    registros[3]["estado"] = reglas.SOLICITANTE_PENDIENTE
    return registros


def _equipos() -> list[dict]:
    catalogo = [
        ("LAP-001", "Notebook Dell Latitude", "laptop", "16 GB RAM, cargador incluido"),
        ("LAP-002", "Notebook Dell Latitude", "laptop", "16 GB RAM, cargador incluido"),
        ("LAP-003", "Notebook Lenovo ThinkPad", "laptop", "8 GB RAM"),
        ("TAB-001", "Tablet Samsung Galaxy Tab", "tablet", "Con lapiz optico"),
        ("TAB-002", "Tablet Samsung Galaxy Tab", "tablet", "Sin lapiz optico"),
        ("ARD-001", "Kit Arduino Uno", "arduino", "Kit completo con protoboard"),
        ("ARD-002", "Kit Arduino Uno", "arduino", "Kit completo con protoboard"),
        ("ARD-003", "Kit Arduino Mega", "arduino", "Incluye sensores"),
        ("PRO-001", "Proyector Epson", "proyector", "Con control remoto y cable HDMI"),
        ("CAM-001", "Camara Canon EOS", "camara", "Con tripode y bateria de repuesto"),
    ]
    return [modelos.nuevo_equipo(*fila) for fila in catalogo]


def _solicitudes() -> list[dict]:
    """Una solicitud por cada estado relevante, para probar sin esperar dias."""
    registros = []

    # 1. Por revisar: bloquea LAP-001 aunque nadie la haya aprobado todavia.
    registros.append(
        modelos.nueva_solicitud(
            "SOL-0001", "12345678-5", ["LAP-001"], HOY + timedelta(days=1), HOY + timedelta(days=6)
        )
    )

    # 2. Aprobada, pendiente de retiro.
    aprobada = modelos.nueva_solicitud(
        "SOL-0002", "17890123-0", ["TAB-001", "ARD-001"], HOY, HOY + timedelta(days=5)
    )
    modelos.registrar_cambio(aprobada, estados.APROBADA, "ENC-0001")
    registros.append(aprobada)

    # 3. En prestamo, dentro de plazo.
    en_prestamo = modelos.nueva_solicitud(
        "SOL-0003", "9876543-3", ["PRO-001"], HOY - timedelta(days=2), HOY + timedelta(days=3)
    )
    modelos.registrar_cambio(en_prestamo, estados.APROBADA, "ENC-0001")
    modelos.registrar_cambio(en_prestamo, estados.EN_PRESTAMO, "ENC-0001")
    registros.append(en_prestamo)

    # 4. Periodo de gracia: vencio ayer, todavia puede renovar o devolver.
    gracia = modelos.nueva_solicitud(
        "SOL-0004", "12345678-5", ["ARD-003"], HOY - timedelta(days=8), HOY - timedelta(days=1)
    )
    modelos.registrar_cambio(gracia, estados.APROBADA, "ENC-0002")
    modelos.registrar_cambio(gracia, estados.EN_PRESTAMO, "ENC-0002")
    modelos.registrar_cambio(gracia, estados.PERIODO_GRACIA, estados.SISTEMA)
    registros.append(gracia)

    # 5. Atrasada: por esto Diana quedo en estado pendiente.
    atrasada = modelos.nueva_solicitud(
        "SOL-0005", "20111222-2", ["CAM-001"], HOY - timedelta(days=12), HOY - timedelta(days=5)
    )
    modelos.registrar_cambio(atrasada, estados.APROBADA, "ENC-0001")
    modelos.registrar_cambio(atrasada, estados.EN_PRESTAMO, "ENC-0001")
    modelos.registrar_cambio(atrasada, estados.PERIODO_GRACIA, estados.SISTEMA)
    modelos.registrar_cambio(atrasada, estados.ATRASADA, estados.SISTEMA)
    registros.append(atrasada)

    # 6. Concluida: no bloquea equipos, sirve para probar los filtros.
    concluida = modelos.nueva_solicitud(
        "SOL-0006", "17890123-0", ["LAP-003"], HOY - timedelta(days=20), HOY - timedelta(days=14)
    )
    modelos.registrar_cambio(concluida, estados.APROBADA, "ENC-0001")
    modelos.registrar_cambio(concluida, estados.EN_PRESTAMO, "ENC-0001")
    modelos.registrar_cambio(concluida, estados.CONCLUIDA, "ENC-0001")
    registros.append(concluida)

    # 7. Rechazada, con motivo.
    rechazada = modelos.nueva_solicitud(
        "SOL-0007", "9876543-3", ["LAP-002"], HOY - timedelta(days=3), HOY + timedelta(days=2)
    )
    modelos.registrar_cambio(rechazada, estados.RECHAZADA, "ENC-0002", "Equipo reservado para clases")
    registros.append(rechazada)

    return registros


def cargar(forzar: bool = False) -> None:
    existentes = [c for c in almacen.COLECCIONES if almacen.ruta(c).exists()]
    if existentes and not forzar:
        print("Ya existen datos en:", ", ".join(existentes))
        print("Use --forzar para sobrescribirlos.")
        raise SystemExit(1)

    almacen.escribir("encargados", _encargados())
    almacen.escribir("solicitantes", _solicitantes())
    almacen.escribir("equipos", _equipos())
    almacen.escribir("solicitudes", _solicitudes())

    print(f"Datos de demostracion escritos en {almacen.ruta('equipos').parent}")
    print(f"  Encargados:   2  (contrasena: {CLAVE_ENCARGADO})")
    print(f"  Solicitantes: 4  (contrasena: {CLAVE_SOLICITANTE})")
    print("  Equipos:      10")
    print("  Solicitudes:  7  (una por estado relevante)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga los datos de demostracion")
    parser.add_argument("--forzar", action="store_true", help="sobrescribe los archivos existentes")
    cargar(parser.parse_args().forzar)
