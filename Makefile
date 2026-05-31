.PHONY: venv install process serve clean

PYTHON := uv run python

venv:
	uv venv

install: venv
	uv pip install -e ".[enrich]"

process:
	$(PYTHON) analyze.py

serve:
	$(PYTHON) -m streamlit run app.py

all: process serve

clean:
	rm -rf data/cache/*.json