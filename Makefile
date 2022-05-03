PIP=venv/Scripts/pip
PYINSTALLER=venv/Scripts/pyinstaller
FLASK=venv/Scripts/flask
PYTEST=venv/Scripts/pytest
PYLINT=venv/Scripts/pylint

venv:
	python3 -m venv venv
	${PIP} install --upgrade pip setuptools wheel

.PHONY: clean-venv
clean-venv:
	rm -rf venv

.PHONY: fresh
fresh: clean-venv venv
	${PIP} install -r requirements.in && \
	${PIP} freeze > requirements.txt

.PHONY: freeze
freeze:
	${PIP} freeze > requirements.txt

.PHONY: lint
lint:
	${PYLINT} commonplace

.PHONY: test
test:
	${PYTEST} tests

.PHONY: start
start:
	FLASK_APP=commonplace.__main__ FLASK_ENV=development ${FLASK} run

.PHONY: pkg
pkg: dist/commonplace.exe

dist/commonplace.exe: venv $(shell find commonplace -type f)
	${PYINSTALLER} --onefile commonplace/__main__.py --name commonplace
	ls -lh dist/commonplace.exe
