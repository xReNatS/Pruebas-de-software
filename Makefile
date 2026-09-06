# Atajos del proyecto. Ejecutar `make` sin argumentos para ver la ayuda.
#
# En Windows no viene `make` instalado. Usa el script equivalente:
#     .\make.ps1 <objetivo>
# Ambos aceptan los mismos nombres de objetivo y hacen exactamente lo mismo.
#
# Si prefieres usar make en Windows, instalalo con `choco install make` y
# ejecutalo desde Git Bash, no desde cmd.exe.

# Elige el interprete: el del entorno virtual si existe, si no el del sistema.
# Se prueban las dos ubicaciones porque venv usa `bin` en Unix y `Scripts` en
# Windows.
ifneq ($(wildcard .venv/bin/python),)
    PYTHON := .venv/bin/python
else ifneq ($(wildcard .venv/Scripts/python.exe),)
    PYTHON := .venv/Scripts/python.exe
else
    PYTHON := python
endif

# Interprete con el que se crea el entorno virtual. Se prefiere el lanzador
# `py` de Windows y luego `python3`, porque en varias maquinas el `python` del
# PATH apunta a una instalacion distinta de la que se quiere usar. Se puede
# forzar otro:  make instalar PY_SISTEMA=python3.12
PY_SISTEMA ?= $(shell command -v py >/dev/null 2>&1 && echo "py -3" \
	|| (command -v python3 >/dev/null 2>&1 && echo python3 || echo python))

PYTEST := $(PYTHON) -m pytest
FECHA := $(shell date +%Y-%m-%d)

.DEFAULT_GOAL := ayuda
.PHONY: ayuda instalar correr probar probar-funcional probar-borde probar-negativo \
        probar-reglas probar-escenario probar-pendientes evidencia demo reiniciar \
        registro limpiar verificar

ayuda:
	@echo ""
	@echo "Sistema de prestamo de equipos - objetivos disponibles"
	@echo ""
	@echo "  make instalar            crea el entorno virtual e instala las dependencias"
	@echo "  make correr              inicia la aplicacion de linea de comando"
	@echo "  make probar              ejecuta toda la suite de pruebas"
	@echo "  make verificar           ejecuta la suite y muestra el resumen por categoria"
	@echo ""
	@echo "  make probar-funcional    solo los casos funcionales"
	@echo "  make probar-borde        solo los casos de borde"
	@echo "  make probar-negativo     solo los casos negativos"
	@echo "  make probar-reglas       solo los casos que combinan reglas"
	@echo "  make probar-escenario    solo el escenario completo"
	@echo "  make probar-pendientes   lista los casos aun marcados xfail"
	@echo ""
	@echo "  make evidencia           guarda la salida de las pruebas en evidencias/"
	@echo "  make demo                regenera los datos de demostracion"
	@echo "  make reiniciar           borra datos y logs, y vuelve a cargar la demo"
	@echo "  make registro            muestra las ultimas lineas del log de eventos"
	@echo "  make limpiar             borra caches, logs y archivos temporales"
	@echo ""
	@echo "Interprete en uso: $(PYTHON)"
	@echo "Si dice solo 'python', todavia no existe el entorno virtual: ejecuta make instalar."
	@echo ""

instalar:
	$(PY_SISTEMA) -m venv .venv
	@.venv/bin/python -m pip install --upgrade pip -q 2>/dev/null || .venv/Scripts/python.exe -m pip install --upgrade pip -q
	@.venv/bin/python -m pip install -r requirements.txt 2>/dev/null || .venv/Scripts/python.exe -m pip install -r requirements.txt
	@echo ""
	@echo "Listo. Los objetivos correr y probar ya usan el entorno virtual."

correr:
	$(PYTHON) main.py

probar:
	$(PYTEST)

probar-funcional:
	$(PYTEST) -m funcional

probar-borde:
	$(PYTEST) -m borde

probar-negativo:
	$(PYTEST) -m negativo

probar-reglas:
	$(PYTEST) -m reglas

probar-escenario:
	$(PYTEST) -m escenario

probar-pendientes:
	@echo "Casos a la espera de que se implemente su requerimiento:"
	@$(PYTEST) -q -rx 2>&1 | grep XFAIL || echo "  Ninguno. Todos los requerimientos estan implementados."

evidencia:
	@mkdir -p evidencias
	$(PYTEST) -v > evidencias/pytest-$(FECHA).txt 2>&1 || true
	@echo "Evidencia guardada en evidencias/pytest-$(FECHA).txt"
	@tail -n 3 evidencias/pytest-$(FECHA).txt

demo:
	$(PYTHON) scripts/cargar_demo.py --forzar

reiniciar:
	@rm -rf data logs
	$(PYTHON) scripts/cargar_demo.py --forzar

registro:
	@tail -n 30 logs/eventos.log 2>/dev/null || echo "Todavia no hay eventos registrados."

limpiar:
	@rm -rf .pytest_cache logs
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "Caches, logs y archivos temporales eliminados. Los datos de data/ se conservan."

# Cuenta los casos de una categoria. Se extrae el primer numero de la linea
# "N/M tests collected" que imprime pytest al recolectar.
contar = $(PYTEST) -m $(1) --collect-only -q 2>/dev/null \
	| grep -oE '[0-9]+/[0-9]+ tests collected' | cut -d/ -f1

verificar: probar
	@echo ""
	@echo "Casos por categoria (minimo exigido por la tarea entre parentesis):"
	@printf "  funcionales (5) : "; $(call contar,funcional)
	@printf "  borde       (4) : "; $(call contar,borde)
	@printf "  negativos   (3) : "; $(call contar,negativo)
	@printf "  reglas      (2) : "; $(call contar,reglas)
	@printf "  escenario   (1) : "; $(call contar,escenario)
