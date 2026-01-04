# AgTools CLI Quickstart

## Start the Backend API

```bash
cd backend
AGTOOLS_DEV_MODE=1 python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000')"
```

Or with auto-reload for development:
```bash
cd backend
AGTOOLS_DEV_MODE=1 uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Start the Desktop App

```bash
python start_agtools.pyw
```

Or use the desktop/start menu shortcuts created during installation.

## Run Tests

```bash
# GenFin workflow tests (54 tests)
python tests/test_genfin_workflow.py

# Farm operations tests (97 tests)
python tests/test_farm_workflow.py

# All tests
python -m pytest tests/
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGTOOLS_DEV_MODE` | `0` | Set to `1` to bypass authentication |
| `AGTOOLS_DB_PATH` | `agtools.db` | SQLite database path |
