PIP=venv/Scripts/pip
PYINSTALLER=venv/Scripts/pyinstaller
FLASK=venv/Scripts/flask
PYTEST=venv/Scripts/pytest
PYLINT=venv/Scripts/pylint
BUILD_NUMBER=0
VERSION=$(shell cat version.txt).${BUILD_NUMBER}

venv:
	python3 -m venv venv
	${PIP} install --upgrade pip setuptools wheel

.PHONY: clean-venv
clean-venv:
	rm -rf venv

install: build/.install

build/.install: venv requirements.txt
	${PIP} install -r requirements.txt && mkdir -p build && touch $@

.PHONY: fresh
fresh: clean-venv venv
	${PIP} install -r requirements.in && \
	${PIP} freeze > requirements.txt

.PHONY: freeze
freeze:
	${PIP} freeze > requirements.txt

.PHONY: lint
lint: install
	${PYLINT} commonplace

.PHONY: test
test: install
	${PYTEST} tests

.PHONY: start
start: install
	FLASK_APP=commonplace.__main__ FLASK_ENV=development ${FLASK} run

.PHONY: update-version
update-version:
	sed 's/^VERSION = .*/VERSION = "${VERSION}"/' commonplace/__main__.py > commonplace/__main__.py.tmp
	diff commonplace/__main__.py commonplace/__main__.py.tmp > /dev/null || mv commonplace/__main__.py.tmp commonplace/__main__.py
	rm -f commonplace/__main__.py.tmp

.PHONY: pkg
pkg: update-version dist/commonplace.exe
	@echo ======================
	@echo "Size: $(shell ls -lh dist/commonplace.exe | awk '{print $$5}')"
	@echo "Version: $(shell dist\commonplace.exe --version)"

dist/commonplace.exe: build/.install $(shell find commonplace -name '*.py')
	${PYINSTALLER} --onefile commonplace/__main__.py --name commonplace
