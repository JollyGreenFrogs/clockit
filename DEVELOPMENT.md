# Development setup

Quick steps to create the development environment and run tests locally.

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

2. Run tests:

```bash
PYTHONPATH=$(pwd) .venv/bin/pytest -q
```

3. Install and run pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
