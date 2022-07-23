VENV_BIN=$(shell [ -d venv/bin ] && echo 'venv/bin' || echo 'venv/Scripts')
PIP=${VENV_BIN}/pip
PYTEST=${VENV_BIN}/pytest
PYLINT=${VENV_BIN}/pylint
BASE_VERSION=0.3.0
BUILD_NUMBER=0
VERSION=${BASE_VERSION}.${BUILD_NUMBER}

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

.PHONY: system_tests
system-test: install
	${PYTEST} system_tests

.PHONY: vscode_extension
vscode_extension: commonplace_vscode/node_modules
	cd commonplace_vscode && \
	npm version ${BASE_VERSION} --allow-same-version && \
	npm run package

commonplace_vscode/node_modules: commonplace_vscode/package.json
	cd commonplace_vscode && \
	npm install --unsafe-perm

.PHONY: update-version
update-version:
	sed 's/^VERSION = .*/VERSION = "${VERSION}"/' commonplace/__main__.py > commonplace/__main__.py.tmp
	diff commonplace/__main__.py commonplace/__main__.py.tmp > /dev/null || mv commonplace/__main__.py.tmp commonplace/__main__.py
	rm -f commonplace/__main__.py.tmp

.PHONY: pkg
pkg: update-version dist/commonplace.tar
	@echo "::set-output name=version::${VERSION}"
	@echo ======================
	@echo "Version: $(shell dist\commonplace.exe --version)"
	@echo "Executable size: $(shell ls -lh dist/commonplace.exe | awk '{print $$5}')"
	@echo "Archive size: $(shell ls -lh dist/commonplace-${VERSION}.tar | awk '{print $$5}')"

dist/commonplace.tar: dist/commonplace.exe config_sample.yml vscode_extension
	cp config_sample.yml dist/config.yml
	touch dist/todo.txt
	cp commonplace_vscode/commonplace.vsix dist/
	cd dist && tar cf "commonplace-${VERSION}.tar" *

.PHONY: release
release:
	git tag v${BASE_VERSION}
	git push origin v${BASE_VERSION}
