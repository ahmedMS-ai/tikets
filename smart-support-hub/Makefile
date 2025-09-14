
run:
	streamlit run app/main.py

format:
	black .
	ruff check --fix . || true

lint:
	ruff check .

test:
	pytest -q
