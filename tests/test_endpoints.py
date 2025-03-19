import os
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test env flag to prevent background thread
os.environ["TESTING"] = "True"

from main import app, get_db
from models import Base, GlucoseReading

# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test tables
Base.metadata.create_all(bind=engine)

# Override dependencies
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client 
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    # Setup: clear data before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown: clear data after each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_get_stats_endpoint():
    """Test the stats endpoint with mock data"""
    # Create session 
    db = TestingSessionLocal()
    
    # Create test data
    test_readings = [
        GlucoseReading(value=60, timestamp=datetime(2025, 1, 1, 12, 0, 0)),
        GlucoseReading(value=100, timestamp=datetime(2025, 1, 1, 12, 5, 0)),
        GlucoseReading(value=200, timestamp=datetime(2025, 1, 1, 12, 10, 0)),
    ]
    
    # Add test data to test database
    for reading in test_readings:
        db.add(reading)
    db.commit()
    db.close()
    
    # Call endpoint
    response = client.get("/stats?hours=24")
    
    # Check Response
    assert response.status_code == 200
    # Verify the response returns some data
    assert response.json()

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Glucose Tracker API"}