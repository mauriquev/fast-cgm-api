import pytest
from datetime import datetime
from models import GlucoseReading


def test_glucose_reading_model():
    """Test the GlucoseReading model properties"""

    timestamp = datetime(2025, 1, 1, 12, 0, 0)
    reading = GlucoseReading(
        value=115,
        timestamp=timestamp,
        trend=4,
        trend_description="Steady",
        trend_arrow="→"
    )
    # Tests that the properties are set correctly

    assert reading.value == 115
    assert reading.timestamp == timestamp
    assert reading.trend == 4
    assert reading.trend_description == "Steady"    
    assert reading.trend_arrow == "→"

    # Tests the string representation
    rep_str = repr(reading)
    assert "GlucoseReading" in rep_str
    assert "115 mg/dL" in rep_str
    assert "2025-01-01 12:00:00" in rep_str
