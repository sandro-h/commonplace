# commonplace

[![CI](https://github.com/sandro-h/commonplace/actions/workflows/ci.yml/badge.svg)](https://github.com/sandro-h/commonplace/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=sandro-h_commonplace&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=sandro-h_commonplace)

## Development

### Testing approach

Where possible, use system tests against the REST API of the running app. Rationale: this makes the test portable against other implementations.

### Note on @commonplace/lib dependencies

We declare date-fns as a *dev* dependency because we explicitly allowed webpack to bundle it with our code (instead of excluding
it as an external). We do this because we can profit from tree  shaking so that we don't need to depend on the full date-fns
library when using the commonplace library.
