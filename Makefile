# ------------------------------------------------------------------
# Helmet Safety Assistant: คำสั่งลัดสำหรับพัฒนาและรันระบบ
# ใช้งาน: make <target>   (พิมพ์ `make` หรือ `make help` เพื่อดูรายการ)
# ------------------------------------------------------------------

SHELL   := /bin/bash
PYTHON  ?= python3.11
VENV    ?= .venv
PY      ?= $(VENV)/bin/python
PIP     ?= $(VENV)/bin/pip
NPM     ?= npm
HOST    ?= 127.0.0.1
PORT    ?= 8000

.DEFAULT_GOAL := help

.PHONY: help install venv backend frontend dev detect eval eval-mock test build up down logs clean

help: ## แสดงรายการคำสั่งทั้งหมด
	@echo "Helmet Safety Assistant: คำสั่งที่ใช้ได้"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "ตัวแปรที่ปรับได้: PY=$(PY)  PYTHON=$(PYTHON)  PORT=$(PORT)"

$(PY):
	$(PYTHON) -m venv $(VENV)

venv: $(PY) ## สร้าง Python virtualenv (.venv) ถ้ายังไม่มี

install: $(PY) ## ติดตั้ง dependencies ทั้งหมด (venv + pip + npm)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r backend/requirements.txt
	cd frontend && $(NPM) install

backend: ## รัน FastAPI backend (http://localhost:8000, docs ที่ /docs)
	$(PY) -m uvicorn backend.main:app --reload --host $(HOST) --port $(PORT)

frontend: ## รัน React dev server (http://localhost:5173)
	cd frontend && $(NPM) run dev

dev: ## รัน backend + frontend พร้อมกัน (กด Ctrl+C เพื่อหยุดทั้งคู่)
	@trap 'kill 0' EXIT; \
		( $(PY) -m uvicorn backend.main:app --reload --host $(HOST) --port $(PORT) ) & \
		( cd frontend && $(NPM) run dev ) & \
		wait

detect: ## ประมวลผลคลิปใน data/clips/ ด้วย YOLOv8 แล้วเขียน data/events.csv
	$(PY) -m backend.detector

eval: ## ประเมินความแม่นยำของผู้ช่วย AI (ใช้ LLM จริงถ้าตั้งค่า LLM_API_KEY ไว้)
	$(PY) -m backend.evaluate

eval-mock: ## ประเมินด้วย mock LLM (ไม่ต้องใช้ API key)
	$(PY) -m backend.evaluate --mock

test: ## รัน unit tests ของ backend (pytest)
	$(PY) -m pytest backend/tests -q

build: ## build frontend สำหรับ production (frontend/dist)
	cd frontend && $(NPM) run build

up: ## รันทั้งระบบด้วย Docker Compose (build ใหม่)
	docker compose up --build

down: ## หยุดและลบ container ของ Docker Compose
	docker compose down

logs: ## ดู log ของ Docker Compose
	docker compose logs -f

clean: ## ลบไฟล์ cache / build (ไม่ลบข้อมูลใน data/)
	find . -type d -name "__pycache__" -not -path "./$(VENV)/*" -not -path "./frontend/node_modules/*" -prune -exec rm -rf {} +
	rm -rf .pytest_cache backend/.pytest_cache frontend/dist
