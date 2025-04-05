# MultiLLM Cost-Optimized API

This project is a microservice that routes prompts to the most cost-effective LLM API with fallback logic.

## Features
- Multiple LLM provider support
- Token & cost tracking
- Fallback on failures
- FastAPI-based API

## How to Run
```bash
pip install -r requirements.txt
uvicorn app:app --reload
