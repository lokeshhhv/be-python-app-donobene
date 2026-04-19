import asyncio
from sqlalchemy import text
from src.db.session import engine

async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("Connection successful: SELECT 1 returned 1")
            else:
                print("Connection failed: Unexpected result")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
