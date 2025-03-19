import pytest 
from unittest.mock import patch, MagicMock
from database import get_db, clean_env

# Creates a test values for the env variables
def test_clean_env():
    """Test the clean_env funtion in database.py"""
    with patch.dict('os.environ', {'TEST_VAR': 'test_value'}):
        result = clean_env('TEST_VAR')
        assert result == 'test_value'
    # Test that it is able to remove quotes form env variables
    with patch.dict('os.environ', {'TEST_VAR': 'quoted_value'}):
        result = clean_env('TEST_VAR')
        assert result == 'quoted_value'


@patch('database.SessionLocal')
def test_get_db(mock_session_local):
    """Test that get_db yields a session and closes it properly"""
    # Mock Setup
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    #Creates a generator object
    gen = get_db()
    # Get the first value from the generator
    # This will execute the code until the first yield
    db = next(gen)
    assert db == mock_db
    # Ensure that close is not called yet
    mock_db.close.assert_not_called()
    # Close the generator
    # This will execute the code after the yield
    try:
        next(gen) 
    except StopIteration:
        pass
    # Ensure that close is called once 
    mock_db.close.assert_called_once()
