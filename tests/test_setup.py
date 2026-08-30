def test_environment_imports():
    import fastapi
    import uvicorn
    import sqlite3
    import pytest
    assert fastapi.__version__ is not None
