install::
	poetry install

lint:: install
	poetry run ruff format --check

fmt:: install
	poetry run ruff format

mypy:: install
	poetry run mypy .

check-all:: lint mypy
