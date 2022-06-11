PIP=venv/Scripts/pip
PYINSTALLER=venv/Scripts/pyinstaller
FLASK=venv/Scripts/flask
PYTEST=venv/Scripts/pytest
PYLINT=venv/Scripts/pylint
BUILD_NUMBER=0
VERSION=$(shell cat version.txt).${BUILD_NUMBER}

venv:
	python3 -m venv venv

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

.PHONY: system_tests
system-test: install
	${PYTEST} system_tests

.PHONY: start
start: install
	COMMONPLACE_CONFIG=system_test_config.yaml \
	FLASK_APP=commonplace.__main__ \
	FLASK_ENV=development \
	${FLASK} run

.PHONY: start-background
start-background: install
	( \
		COMMONPLACE_CONFIG=system_test_config.yaml \
		FLASK_APP=commonplace.__main__ \
		FLASK_ENV=development \
		${FLASK} run > commonplace.log 2>&1 & \
	)

.PHONY: update-version
update-version:
	sed 's/^VERSION = .*/VERSION = "${VERSION}"/' commonplace/__main__.py > commonplace/__main__.py.tmp
	diff commonplace/__main__.py commonplace/__main__.py.tmp > /dev/null || mv commonplace/__main__.py.tmp commonplace/__main__.py
	rm -f commonplace/__main__.py.tmp

.PHONY: pkg
pkg: update-version dist/commonplace.tar
	@echo ======================
	@echo "Version: $(shell dist\commonplace.exe --version)"
	@echo "Executable size: $(shell ls -lh dist/commonplace.exe | awk '{print $$5}')"
	@echo "Archive size: $(shell ls -lh dist/commonplace-${VERSION}.tar | awk '{print $$5}')"

dist/commonplace.tar: dist/commonplace.exe config_sample.yml
	cp config_sample.yml dist/config.yml
	touch dist/todo.txt
	cd dist && tar cf "commonplace-${VERSION}.tar" *

dist/commonplace.exe: build/.install $(shell find commonplace -name '*.py') icon.png
	${PYINSTALLER} \
		--icon icon.png \
		--onefile commonplace/__main__.py \
		--name commonplace
