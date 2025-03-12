from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from datetime import datetime

from database import Base

class GlucoseReadings(Base):
    __tablename__ = 'glucose_readings'

    id = Column(Integer, primary_key=True, index=True)

    # Glucose value in mg/dL
    value = Column(Float, nullable=False)

    # Timestamp of the reading
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Trend information from Dexcom
    trend = Column(Integer, nullable=True)
    trend_description = Column(String, nullable=True)
    trend_arrow = Column(String, nullable=True)

    def __repr__(self):
        """String representation of a reading""" 
        return f"<GlucoseReading: {self.value} mg/dL at {self.timestamp}>"
        # example: <GlucoseReading: 100 mg/dL at 2021-01-01 00:00:00>

