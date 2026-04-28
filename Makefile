.PHONY: all analysis test

all: analysis

analysis:
	python analysis/recompute_tables_day4.py

test:
	python -m unittest discover -s tests
