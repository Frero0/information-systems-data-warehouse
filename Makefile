PYTHON ?= python3
DATABASE ?= si_demo
PSQL ?= psql

.PHONY: test check sql-check analyze package

test:
	$(PYTHON) -m unittest discover -s tests -v

check: test
	$(PYTHON) scripts/validate_project.py

sql-check:
	$(PYTHON) scripts/check_sql.py --database $(DATABASE) --psql $(PSQL)

analyze:
	$(PYTHON) scripts/analyze.py --database $(DATABASE) --psql $(PSQL)

package:
	$(PYTHON) scripts/package_workflow.py
