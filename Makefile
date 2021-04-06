POETRY := poetry run

lint:
	$(POETRY) pylint vim_clutchify
	cd tests && $(POETRY) pylint tests
	$(POETRY) mypy vim_clutchify tests

REPORT := term-missing:skip-covered
test:
	$(POETRY) pytest --cov=vim_clutchify --cov-report=$(REPORT)
