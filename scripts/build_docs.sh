#!/usr/bin/env bash
set -euo pipefail
mkdocs build --config-file docs_site/mkdocs.yml --clean
