# fast-cgm-api
FastAPI Dexcom G7 python application to retrieve ans store data in PostgreSQL


## Packages
The packages that this application will be using:
IMPORTANT read the pydexcom for the initial setup using dexcom api
- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary
- pydexcom (https://github.com/gagebenne/pydexcom)


# Functionality 
The app automatically retrieves glucose readings from Dexcom's API and stores them in a PostgreSQL database. You can access the historical readings from the last 24 hours, and every week you'll get an average of the readings from that period. The app also provides statistical analysis including time-in-range percentages and daily averages to help track glucose patterns over time.

### Metrics provided:

- Glucose value 
- Timestamp of each reading
- Trend description (e.g., steady, rising slightly)
- Trend arrow visualization
- Time in range percentages (within 70-180 mg/dL)
- Min, max, and average glucose values

Features a background synchronization process that runs every 5 minutes to ensure your data stays current. You can also manually trigger synchronization when needed. Additional features include the ability to add notes to specific readings and access detailed statistics through API endpoints designed for Grafana dashboard integration.