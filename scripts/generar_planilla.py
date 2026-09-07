"""Genera la planilla de casos de prueba a partir de la suite real.

Uso:  python scripts/generar_planilla.py

Escribe evidencias/planilla-casos-de-prueba.csv, listo para pegar en la planilla
del Aula, y docs/casos-de-prueba.md con la misma tabla en formato legible.

La planilla se genera y no se escribe a mano a proposito. Un caso que solo tenga
el resultado esperado se considera incompleto, asi que el resultado obtenido y
el estado salen de ejecutar la suite de verdad, no de lo que alguien recuerde.
Si un caso se agrega, se renombra o cambia de categoria, basta con volver a
ejecutar esto.
"""

import ast
import csv
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_PRUEBAS = RAIZ / "tests"
SALIDA_CSV = RAIZ / "evidencias" / "planilla-casos-de-prueba.csv"
SALIDA_MD = RAIZ / "docs" / "casos-de-prueba.md"

CATEGORIAS = {
    "funcional": "Funcional",
    "borde": "Borde",
    "negativo": "Negativo",
    "reglas": "Combina reglas",
    "escenario": "Escenario completo",
}

# Requerimiento que verifica cada caso. Es la trazabilidad exigida por la tarea,
# asi que se declara explicitamente en vez de adivinarla desde el nombre.
REQUERIMIENTO = {
    **dict.fromkeys(["CP-01", "CP-02", "CP-03", "CP-04", "CP-05"], "RF01"),
    **dict.fromkeys(["CP-06", "CP-07", "CP-08", "CP-09"], "RN15"),
    **dict.fromkeys(["CP-10", "CP-11", "CP-12", "CP-13"], "RN12"),
    **dict.fromkeys(["CP-14", "CP-15"], "VAL01"),
    **dict.fromkeys(["CP-16", "CP-17", "CP-18"], "RF02"),
    **dict.fromkeys(["CP-19", "CP-20", "CP-21", "CP-22"], "RF03"),
    "CP-23": "RF04",
    **dict.fromkeys(["CP-24", "CP-25", "CP-26", "CP-27", "CP-28", "CP-29", "CP-30", "CP-31"], "RF05"),
    "CP-32": "RF06, RF07",
    "CP-33": "RF07",
    "CP-34": "RF09",
    "CP-35": "RF08, RF10",
    "CP-36": "RF11",
    "CP-37": "RF08",
    "CP-38": "RF05, RF07, RF08, RF10",
    "CP-39": "INF02",
    **dict.fromkeys(["CP-40", "CP-41", "CP-43"], "INF01"),
    "CP-42": "INF02",
    "CP-44": "DEM02",
    **dict.fromkeys(["CP-45", "CP-46", "CP-47"], "DEM01"),
    **dict.fromkeys(["CP-48", "CP-49"], "DEM02"),
    "CP-50": "RN01",
    "CP-51": "RN02",
    "CP-52": "RF05",
    "CP-53": "RF05",
    "CP-54": "RF05, RN12",
    "CP-55": "RF05",
    **dict.fromkeys(["CP-56", "CP-57", "CP-58", "CP-59"], "RF09"),
    **dict.fromkeys(["CP-60", "CP-61"], "RF07"),
    "CP-62": "RF06",
    **dict.fromkeys(["CP-63", "CP-64", "CP-65", "CP-66", "CP-67", "CP-68"], "RF08"),
    **dict.fromkeys(["CP-69", "CP-70", "CP-71"], "RF10"),
    **dict.fromkeys(["CP-72", "CP-73"], "RF11"),
    **dict.fromkeys(["CP-74", "CP-75", "CP-76", "CP-77"], "AUT"),
}

# Issue donde esta registrado cada defecto abierto. Une el caso que falla con
# su reporte, que es lo que la tarea pide para la seccion de defectos.
DEFECTO_REGISTRADO = {
    "CP-50": "#27",
    "CP-51": "#28",
    "CP-52": "#29",
}

# Que significa cada fixture como precondicion, en lenguaje de la planilla.
PRECONDICIONES = {
    "datos_base": "Un encargado, dos solicitantes al día y tres equipos libres",
    "catalogo_amplio": "Los datos base más tres unidades extra, dos de ellas laptops",
    "demo_cargada": "El escenario de demostración completo recién cargado",
    "entorno_aislado": "Directorio de datos y de logs vacíos",
    "sesion_encargado": "Sesión iniciada como encargado",
    "sesion_ana": "Sesión iniciada como la solicitante Ana Pérez",
    "sesion_bruno": "Sesión iniciada como el solicitante Bruno Silva",
    "crear_solicitud_directa": "Se insertan solicitudes en un estado dado sin pasar por los servicios",
    "capsys": "Se captura la salida por pantalla",
    "solicitudes_sembradas": "Una solicitud por cada estado que los filtros deben distinguir",
    "con_solicitud": "Una solicitud de Ana sobre LAP-001, en el estado que el caso necesite",
    "sembrar": "Una solicitud de Ana sobre LAP-001, en el estado y las fechas que el caso necesite",
}


def recolectar_casos() -> dict[str, dict]:
    """Lee los archivos de prueba y extrae un registro por caso."""
    casos: dict[str, dict] = {}

    for archivo in sorted(DIR_PRUEBAS.glob("test_*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in arbol.body:
            if not isinstance(nodo, ast.FunctionDef) or not nodo.name.startswith("test_cp"):
                continue

            identificador = "CP-" + nodo.name[7:9]
            marcas, defecto = _leer_decoradores(nodo)
            documentacion = ast.get_docstring(nodo) or ""
            primera, _, resto = documentacion.partition("\n")

            casos[identificador] = {
                "id": identificador,
                "requerimiento": REQUERIMIENTO.get(identificador, "sin mapear"),
                "categoria": ", ".join(CATEGORIAS.get(m, m) for m in marcas) or "sin categoría",
                "archivo": f"tests/{archivo.name}",
                "funcion": nodo.name,
                "linea": nodo.lineno,
                "precondicion": _precondiciones(nodo),
                "esperado": re.sub(r"^CP-\d+:\s*", "", primera).strip(),
                "nota": " ".join(resto.split()).strip(),
                "defecto_conocido": defecto,
                "obtenido": "no ejecutado",
                "estado": "sin ejecutar",
                "ejecuciones": 0,
            }
    return casos


def _leer_decoradores(nodo: ast.FunctionDef) -> tuple[list[str], str]:
    """Devuelve las marcas de categoría y el motivo del xfail si lo hay."""
    marcas, defecto = [], ""
    for decorador in nodo.decorator_list:
        texto = ast.unparse(decorador)
        for nombre in CATEGORIAS:
            if f"pytest.mark.{nombre}" in texto:
                marcas.append(nombre)
        if "xfail" in texto:
            coincidencia = re.search(r"reason=['\"](.+?)['\"]", texto)
            defecto = coincidencia.group(1) if coincidencia else "defecto abierto"
    return marcas, defecto


def _precondiciones(nodo: ast.FunctionDef) -> str:
    descripciones = [
        PRECONDICIONES[arg.arg] for arg in nodo.args.args if arg.arg in PRECONDICIONES
    ]
    return ". ".join(descripciones) if descripciones else "Ninguna"


def ejecutar_suite(casos: dict[str, dict]) -> Path:
    """Corre pytest y vuelca el resultado real de cada caso en los registros."""
    # Se cierra el descriptor de inmediato: en Windows no se puede borrar un
    # archivo que sigue abierto, y pytest lo abre por su cuenta.
    descriptor, ruta = tempfile.mkstemp(suffix=".xml")
    os.close(descriptor)
    reporte = Path(ruta)
    salida = RAIZ / "evidencias" / "ejecucion-suite.txt"
    salida.parent.mkdir(parents=True, exist_ok=True)

    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", f"--junit-xml={reporte}"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    salida.write_text(proceso.stdout, encoding="utf-8")

    for caso in ET.parse(reporte).getroot().iter("testcase"):
        identificador = _id_desde_nombre(caso.get("name", ""))
        if identificador not in casos:
            continue
        registro = casos[identificador]
        registro["ejecuciones"] += 1
        _acumular(registro, caso)

    reporte.unlink(missing_ok=True)
    return salida


def _id_desde_nombre(nombre: str) -> str:
    coincidencia = re.match(r"test_cp(\d\d)", nombre)
    return f"CP-{coincidencia.group(1)}" if coincidencia else ""


def _acumular(registro: dict, caso: ET.Element) -> None:
    """Un caso parametrizado corre varias veces; el peor resultado manda."""
    if caso.find("failure") is not None or caso.find("error") is not None:
        registro["obtenido"] = "Falló la comprobación"
        registro["estado"] = "Fallido"
        return
    omitido = caso.find("skipped")
    if omitido is not None and omitido.get("type", "").endswith("xfail"):
        if registro["estado"] != "Fallido":
            reporte = DEFECTO_REGISTRADO.get(registro["id"])
            registro["obtenido"] = (
                f"Falla como se esperaba. {registro['defecto_conocido']}"
                + (f". Registrado en {reporte}" if reporte else "")
            )
            registro["estado"] = (
                f"Defecto abierto {reporte}" if reporte else "Pendiente de implementar"
            )
        return
    if registro["estado"] in ("sin ejecutar", "Aprobado"):
        registro["obtenido"] = "Coincide con el resultado esperado"
        registro["estado"] = "Aprobado"


COLUMNAS = [
    ("id", "ID"),
    ("requerimiento", "Requerimiento"),
    ("categoria", "Categoría"),
    ("precondicion", "Precondición"),
    ("pasos", "Pasos"),
    ("esperado", "Resultado esperado"),
    ("obtenido", "Resultado obtenido"),
    ("estado", "Estado"),
    ("evidencia", "Evidencia"),
]


def completar(caso: dict) -> dict:
    veces = f" ({caso['ejecuciones']} combinaciones de datos)" if caso["ejecuciones"] > 1 else ""
    caso["pasos"] = f"python -m pytest {caso['archivo']}::{caso['funcion']}{veces}"
    caso["evidencia"] = f"{caso['archivo']}:{caso['linea']} y evidencias/ejecucion-suite.txt"
    return caso


def escribir_csv(casos: list[dict]) -> None:
    SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow([titulo for _clave, titulo in COLUMNAS])
        for caso in casos:
            escritor.writerow([caso[clave] for clave, _titulo in COLUMNAS])


def escribir_markdown(casos: list[dict], salida_suite: Path) -> None:
    conteo: dict[str, int] = {}
    for caso in casos:
        for categoria in caso["categoria"].split(", "):
            conteo[categoria] = conteo.get(categoria, 0) + 1

    lineas = [
        "# Casos de prueba",
        "",
        "**Este archivo se genera. No lo edites a mano.** Para regenerarlo:",
        "",
        "```bash",
        "make planilla          # Linux o macOS",
        ".\\make.ps1 planilla    # Windows",
        "```",
        "",
        "El resultado obtenido y el estado salen de ejecutar la suite, no de lo que",
        "alguien recuerde. La versión para la planilla del Aula está en",
        "`evidencias/planilla-casos-de-prueba.csv`, con punto y coma como separador.",
        "",
        f"Total: **{len(casos)} casos**. "
        f"Aprobados: {sum(1 for c in casos if c['estado'] == 'Aprobado')}. "
        f"Con defecto abierto: {sum(1 for c in casos if c['estado'].startswith('Defecto'))}. "
        f"A la espera de su requerimiento: "
        f"{sum(1 for c in casos if c['estado'] == 'Pendiente de implementar')}. "
        f"Fallidos: {sum(1 for c in casos if c['estado'] == 'Fallido')}.",
        "",
        "## Cobertura por categoría",
        "",
        "| Categoría | Mínimo exigido | Casos |",
        "| --- | --- | --- |",
    ]
    minimos = {"Funcional": 5, "Borde": 4, "Negativo": 3, "Combina reglas": 2, "Escenario completo": 1}
    for categoria, minimo in minimos.items():
        lineas.append(f"| {categoria} | {minimo} | {conteo.get(categoria, 0)} |")

    lineas += [
        "",
        "Un caso puede pertenecer a más de una categoría, así que la suma supera el",
        "total de casos.",
        "",
        "## Detalle",
        "",
        "| " + " | ".join(t for _c, t in COLUMNAS) + " |",
        "| " + " | ".join("---" for _ in COLUMNAS) + " |",
    ]
    for caso in casos:
        celdas = [str(caso[clave]).replace("|", "\\|") for clave, _t in COLUMNAS]
        lineas.append("| " + " | ".join(celdas) + " |")

    lineas += ["", f"Evidencia de la ejecución: `{salida_suite.relative_to(RAIZ).as_posix()}`.", ""]
    SALIDA_MD.write_text("\n".join(lineas), encoding="utf-8")


def main() -> int:
    casos = recolectar_casos()
    print(f"Casos encontrados: {len(casos)}")

    salida_suite = ejecutar_suite(casos)
    ordenados = [completar(casos[k]) for k in sorted(casos, key=lambda x: int(x[3:]))]

    sin_ejecutar = [c["id"] for c in ordenados if c["estado"] == "sin ejecutar"]
    if sin_ejecutar:
        print(f"AVISO: sin resultado de ejecucion: {', '.join(sin_ejecutar)}")
    sin_mapear = [c["id"] for c in ordenados if c["requerimiento"] == "sin mapear"]
    if sin_mapear:
        print(f"AVISO: sin requerimiento asociado: {', '.join(sin_mapear)}")

    escribir_csv(ordenados)
    escribir_markdown(ordenados, salida_suite)

    print(f"  {SALIDA_CSV.relative_to(RAIZ)}")
    print(f"  {SALIDA_MD.relative_to(RAIZ)}")
    print(f"  {salida_suite.relative_to(RAIZ)}")
    resumen: dict[str, int] = {}
    for caso in ordenados:
        resumen[caso["estado"]] = resumen.get(caso["estado"], 0) + 1
    for estado, cantidad in sorted(resumen.items()):
        print(f"  {estado}: {cantidad}")
    return 1 if sin_ejecutar or sin_mapear else 0


if __name__ == "__main__":
    sys.exit(main())
