.PHONY: install test eval api ui docker

install:
	pip install -r requirements-dev.txt -r requirements-ui.txt

test:
	pytest -q

eval:
	python cli.py evaluate --write-report docs/EVALUATION.md

api:
	uvicorn src.app:app --reload

ui:
	streamlit run ui/streamlit_app.py

docker:
	docker compose up --build
