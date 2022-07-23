VENV_BIN=$(shell [ -d venv/bin ] && echo 'venv/bin' || echo 'venv/Scripts')
PIP=${VENV_BIN}/pip
PYTEST=${VENV_BIN}/pytest
PYLINT=${VENV_BIN}/pylint
BASE_VERSION=0.4.0
BUILD_NUMBER=0
VERSION=${BASE_VERSION}.${BUILD_NUMBER}

###################################################################
# Core code
###################################################################

.PHONY: dependencies
dependencies:
ifeq ($(CI),true)
	npm ci
else
	npm install
endif

.PHONY: core
core:
	npm run compile -ws
	cd core/lib && npm run package

.PHONY: test
test:
	npm run test -ws

.PHONY: start-test-server
start-test-server:
	cd core/test_server && npm run serve

###################################################################
# VSCode extension
###################################################################

.PHONY: vscode-extension
vscode-extension: vscode_extension/node_modules
	cd vscode_extension && \
	npm version ${BASE_VERSION} --allow-same-version && \
	npm run package

vscode_extension/node_modules: vscode_extension/package.json
	cd vscode_extension && npm install --save ../core/lib/dist/commonplace-lib-1.0.0.tgz

ifeq ($(CI),true)
	cd vscode_extension && npm ci
else
	cd vscode_extension && npm install
endif

###################################################################
# Python system tests
###################################################################

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

###################################################################
# Release
###################################################################

.PHONY: print-version
print-version:
	@echo "::set-output name=version::${VERSION}"

.PHONY: release
release:
	git tag v${BASE_VERSION}
	git push origin v${BASE_VERSION}
