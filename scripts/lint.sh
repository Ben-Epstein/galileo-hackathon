#!/bin/sh -ex

mypy api
flake8 api tests
black api tests --check
isort api tests scripts --check-only
