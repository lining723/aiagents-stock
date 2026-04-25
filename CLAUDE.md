# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Agents Stock is a multi-AI agent stock analysis system that simulates a securities analyst team. It provides comprehensive stock investment analysis and decision recommendations using multiple AI agents working collaboratively.

## Architecture

The project has two deployment modes:
1. **Streamlit Version** (legacy): Single-process Python app using Streamlit UI
2. **FastAPI + React Version** (current): Separate backend and frontend

### Backend (FastAPI)
- Entry point: `backend/main.py`
- API routes: `backend/api/v1/` (stock, longhubang, monitor, analysis)
- Core config: `backend/core/config.py`
- Schemas: `backend/schemas/`

### Frontend (React + TypeScript)
- Entry point: `frontend/src/main.tsx`
- Pages: `frontend/src/pages/`
- Components: `frontend/src/components/`
- API services: `frontend/src/services/`
- State management: Zustand stores in `frontend/src/stores/`
- Build tool: Vite

### Shared Business Logic (Legacy Structure)
The project retains shared business modules used by both versions:
- `agents/` - AI agent implementations (DeepSeek client, multi-agent collaboration)
- `data/` - Data fetching modules (stock data, fund flow, news)
- `services/` - Business logic services (monitoring, notifications)
- `strategies/` - Trading strategies (low price bull, value stock)
- `db/` - Database modules (SQLite, MongoDB)
- `config/` - Configuration management
- `utils/` - Utilities (logger, PDF generation)

## Common Commands

### Start Backend (FastAPI)
```bash
# Set PYTHONPATH and run
PYTHONPATH=backend python -m backend.main

# Or from project root with virtual environment
source venv/bin/activate
PYTHONPATH=backend uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Start Frontend (React)
```bash
cd frontend
npm install  # First time
npm run dev
```
Frontend runs at: http://localhost:5173

### Start Streamlit Version (Legacy)
```bash
streamlit run app.py --server.port 8503
```

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# Or with Chinese mirror (faster in China)
docker build -f "Dockerfile国内源版" -t agentsstock1 .
docker run -d -p 8503:8501 -v $(pwd)/.env:/app/.env --name agentsstock1 agentsstock1
```

### Run Tests
```bash
# Individual test files
python tests/test_imports.py
python tests/test_logger.py
```

## Environment Configuration

Required environment variables in `.env`:
- `DEEPSEEK_API_KEY` - DeepSeek API key (required)
- `DEEPSEEK_BASE_URL` - API base URL (default: https://api.deepseek.com/v1)
- `DEFAULT_MODEL_NAME` - AI model name (default: deepseek-chat)
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DB_NAME` - MongoDB database name

Optional:
- `TUSHARE_TOKEN` - Tushare data API token
- `TDX_BASE_URL` - TDX local data source API
- `EMAIL_*` - Email notification settings
- `WEBHOOK_*` - DingTalk/Feishu webhook settings

## Key Technical Details

### AI Model Integration
- Uses OpenAI-compatible API interface
- Supports DeepSeek, Qwen, GPT-4o via `DEFAULT_MODEL_NAME` in `.env`
- Agent implementations in `agents/ai_agents.py` and `agents/deepseek_client.py`

### Data Sources
Primary: AKShare (free), yfinance (US stocks)
Fallback: Tushare (requires token), TDX (local deployment)
Data fetching: `data/stock_data.py`

### Database
- SQLite for local storage (monitoring, analysis history)
- MongoDB for persistent storage (optional)
- Database modules in `db/`

### Logging
Unified logging system outputs to both console and `log/app.log`:
```python
from utils.logger import get_logger
logger = get_logger(__name__)
```

### Adding New API Endpoints
1. Create route file in `backend/api/v1/`
2. Define Pydantic schemas in `backend/schemas/`
3. Register router in `backend/main.py`

### Adding New Frontend Pages
1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Create API service function in `frontend/src/services/`

## Stock Code Formats
- A-shares: 6-digit code (e.g., 000001, 600036)
- HK stocks: 1-5 digit code (e.g., 700, 9988)
- US stocks: Letter ticker (e.g., AAPL, TSLA)
