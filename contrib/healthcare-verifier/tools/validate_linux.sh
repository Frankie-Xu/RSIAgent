#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
image="${RSI_HEALTHCARE_IMAGE:-python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e}"
# No bind mounts, credentials, .git or local result directories enter the guest.
COPYFILE_DISABLE=1 tar --exclude='__pycache__' --exclude='.pytest_cache' \
  -cf - core explore env llm benchmarks config scripts tools tests docs \
  contrib/healthcare-verifier requirements.txt requirements-dev.txt pytest.ini \
  run_ale.py run_osworld.py README.md LICENSE .python-version .env.example |
docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges "$image" sh -eu -c '
  mkdir /workspace
  cd /workspace
  tar --no-same-owner --warning=no-unknown-keyword -xf -
  python --version
  uname -a
  python -m pip install --disable-pip-version-check -r requirements-dev.txt -c contrib/healthcare-verifier/tools/requirements-linux.lock
  python -m pip freeze
  python tools/check_rsi_release.py
  python -m pytest -q contrib/healthcare-verifier/tests
  python -m compileall -q contrib/healthcare-verifier
'
