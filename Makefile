PYTHON := .venv/bin/python

.PHONY: fetch data backtest test all

fetch:
	$(PYTHON) data/fetch.py

data:
	$(PYTHON) data/make_patients.py

backtest:
	$(PYTHON) eval/backtest.py

test:
	$(PYTHON) -m pytest tests/ -v

all: fetch data test backtest
