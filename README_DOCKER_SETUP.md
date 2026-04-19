# Production Docker Setup for FastAPI + MySQL

## Recommended Project Structure

```
be-python-app-donobene/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README_DOCKER_SETUP.md
├── src/
│   ├── main.py
│   ├── ... (your FastAPI app code)
│   └── db/
│       └── connection.py  # DB connection sample
```

## Usage

1. Build and start containers:
   ```sh
   docker-compose up --build
   ```
2. FastAPI will be available at http://localhost:8000
3. MySQL will be available at localhost:3306 (inside Docker network as 'db')

## Environment Variables
- DB_HOST (default: db)
- DB_PORT (default: 3306)
- DB_USER (default: root)
- DB_PASSWORD (default: root)
- DB_NAME (default: testdb)

## Sample DB Connection Code (`src/db/connection.py`)

```
import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'testdb'),
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
```

## Best Practices
- Use `.env` files for local development (add to `.gitignore`).
- Use Docker secrets or environment variables for production credentials.
- Use persistent volumes for MySQL data.
- Use `depends_on` with `condition: service_healthy` for proper startup order.
- Set `restart: always` for production resilience.
