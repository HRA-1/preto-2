.PHONY: install start run docker-build docker-run docker-run-prod docker-stop

IMAGE_NAME = preto-2
CONTAINER_NAME = preto-2-container

# Local development
install:
	pip install -r requirements.txt

start:
	streamlit run src/app.py

run: start

# Docker commands
docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8501:8501 \
		-p 8888:8888 \
		-v $(PWD)/src:/app/src \
		-v $(PWD)/notebooks:/app/notebooks \
		-e ENVIRONMENT=dev \
		$(IMAGE_NAME)
	@echo "Streamlit: http://localhost:8501"
	@echo "Jupyter:   http://localhost:8888"

docker-run-prod:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8501:8501 \
		-e ENVIRONMENT=prod \
		-e STREAMLIT_DEV_MODE=false \
		$(IMAGE_NAME)
	@echo "Streamlit: http://localhost:8501"

docker-stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

docker-logs:
	docker logs -f $(CONTAINER_NAME)

docker-shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash
