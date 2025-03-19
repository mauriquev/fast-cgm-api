from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydexcom import Dexcom
from datetime import datetime, timedelta
from typing import List, Optional
import models
from database import engine, get_db
from pydantic import BaseModel
import threading
import time
import os

# Dexcom credentials from environment variables
DEXCOM_USERNAME = os.environ.get("DEXCOM_USERNAME", "")
DEXCOM_PASSWORD = os.environ.get("DEXCOM_PASSWORD", "")

# Create database tables
def setup_database():
    models.Base.metadata.create_all(bind=engine)

# Creates FastAPI application
app = FastAPI(title="Fast CGM API")

# Pydantic model for response data
class GlucoseReadingResponse(BaseModel):
    id: int
    value: float
    timestamp: datetime
    trend: Optional[int] = None
    trend_description: Optional[str] = None
    trend_arrow: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        orm_mode = True  # Allows the Pydantic model to read data from ORM objects

# Function to connect to Dexcom, creates connection to Dexcom API
def get_dexcom():
    try:
        if not DEXCOM_USERNAME or not DEXCOM_PASSWORD:
            raise ValueError("Dexcom credentials not set. Please set DEXCOM_USERNAME and DEXCOM_PASSWORD environment variables.")
    
        dexcom = Dexcom(username=DEXCOM_USERNAME, password=DEXCOM_PASSWORD)
        return dexcom
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Dexcom: {str(e)}")

# Background thread function to sync data (infinite loop)
def sync_dexcom_data():
    """Background thread function to sync data from Dexcom periodically"""
    while True:
        try:
            # Create a new DB session for this thread
            from database import SessionLocal
            db = SessionLocal()
            
            # Get Dexcom data with keyword arguments
            dexcom = Dexcom(username=DEXCOM_USERNAME, password=DEXCOM_PASSWORD)
            glucose = dexcom.get_current_glucose_reading()
            
            if glucose:
                # Check if we already have this reading
                existing = db.query(models.GlucoseReading).filter(
                    models.GlucoseReading.timestamp == glucose.datetime
                ).first()
                
                if not existing:
                    # Save new reading
                    new_reading = models.GlucoseReading(
                        value=glucose.value,
                        timestamp=glucose.datetime,
                        trend=glucose.trend,
                        trend_description=glucose.trend_description,
                        trend_arrow=getattr(glucose, 'trend_arrow', None)
                    )
                    db.add(new_reading)
                    db.commit()
                    print(f"Added new reading: {glucose.value} at {glucose.datetime}")
            
            db.close()
            
        except Exception as e:
            print(f"Error syncing data: {str(e)}")
        
        # Wait 5 minutes before next sync
        time.sleep(300)

# Start background sync thread when app starts
@app.on_event("startup")
def startup_event():
    """Runs when the FastAPI application starts up"""
    setup_database()

    thread = threading.Thread(target=sync_dexcom_data, daemon=True)
    thread.start()

# Root endpoint almost like a healthcheck
@app.get("/")
def read_root():
    """Welcome message endpoint"""
    return {"message": "Welcome to the Glucose Tracker API"}

# Get current glucose reading
@app.get("/readings/current", response_model=GlucoseReadingResponse)
def get_current_reading(db: Session = Depends(get_db)):
    """Get the most recent glucose reading"""
    # First try to get from database
    reading = db.query(models.GlucoseReading).order_by(
        models.GlucoseReading.timestamp.desc()
    ).first()
    
    # If no readings in database, gets it from Dexcom 
    if not reading:
        dexcom = get_dexcom()
        glucose = dexcom.get_current_glucose_reading()
        
        if not glucose:
            raise HTTPException(status_code=404, detail="No glucose reading available")
            
        # If  a new reading it fetched saves it to the database
        reading = models.GlucoseReading(
            value=glucose.value,
            timestamp=glucose.datetime,
            trend=glucose.trend,
            trend_description=glucose.trend_description,
            trend_arrow=getattr(glucose, 'trend_arrow', None)  # Safe attribute access
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
    
    return reading

# Get recent readings
@app.get("/readings/recent", response_model=List[GlucoseReadingResponse])
def get_recent_readings(hours: int = 24, db: Session = Depends(get_db)):
    """Get glucose readings from the past X hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(models.GlucoseReading).filter(
        models.GlucoseReading.timestamp >= cutoff
    ).order_by(models.GlucoseReading.timestamp.desc()).all()
    
    return readings

# Sync readings from Dexcom
@app.post("/sync")
def sync_readings(db: Session = Depends(get_db)):
    """Manually sync readings from Dexcom"""
    dexcom = get_dexcom()
    # Get readings from the last 24 hours (1440 minutes)
    readings = dexcom.get_glucose_readings(minutes=1440)
    
    count = 0
    for glucose in readings:
        # Checks if reading already exists
        existing = db.query(models.GlucoseReading).filter(
            models.GlucoseReading.timestamp == glucose.datetime
        ).first()
        
        if not existing:
            # Save new reading
            new_reading = models.GlucoseReading(
                value=glucose.value,
                timestamp=glucose.datetime,
                trend=glucose.trend,
                trend_description=glucose.trend_description,
                trend_arrow=getattr(glucose, 'trend_arrow', None)
            )
            db.add(new_reading)
            count += 1
    
    db.commit()
    return {"message": f"Synced {count} new readings"}

# Get statistics for Grafana
@app.get("/stats")
def get_stats(hours: int = 24, db: Session = Depends(get_db)):
    """Get statistics about glucose readings for Grafana"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(models.GlucoseReading).filter(
        models.GlucoseReading.timestamp >= cutoff
    ).all()
    
    if not readings:
        return {"message": "No readings available"}
    
    values = [r.value for r in readings]
    in_range = sum(1 for v in values if 70 <= v <= 180)
    below_range = sum(1 for v in values if v < 70)
    above_range = sum(1 for v in values if v > 180)
    
    return {
        "count": len(readings),
        "average": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "median": sorted(values)[len(values) // 2],
        "time_in_range_percent": (in_range / len(readings)) * 100 if readings else 0,
        "time_below_range_percent": (below_range / len(readings)) * 100 if readings else 0,
        "time_above_range_percent": (above_range / len(readings)) * 100 if readings else 0,
        "readings_per_hour": len(readings) / hours
    }

# Add a note to a reading
@app.post("/readings/{reading_id}/note")
def add_note(reading_id: int, note: str, db: Session = Depends(get_db)):
    """Add a note to a specific glucose reading"""
    reading = db.query(models.GlucoseReading).filter(models.GlucoseReading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    reading.notes = note
    db.commit()
    return {"message": "Note added successfully"}

# Get daily averages for the past week
@app.get("/stats/daily")
def get_daily_stats(days: int = 7, db: Session = Depends(get_db)):
    """Get daily glucose statistics for the past X days"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    readings = db.query(models.GlucoseReading).filter(
        models.GlucoseReading.timestamp >= cutoff
    ).all()
    
    if not readings:
        return {"message": "No readings available"}
    
    # Group readings by day
    daily_readings = {}
    for reading in readings:
        # Convert to local date (without time)
        day = reading.timestamp.date()
        if day not in daily_readings:
            daily_readings[day] = []
        daily_readings[day].append(reading.value)
    
    # Calculate stats for each day
    result = []
    for day, values in daily_readings.items():
        in_range = sum(1 for v in values if 70 <= v <= 180)
        result.append({
            "date": day.isoformat(),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
            "time_in_range_percent": (in_range / len(values)) * 100
        })
    
    # Sort by date
    result.sort(key=lambda x: x["date"])
    return result
if __name__ == "__main__":
    setup_database()