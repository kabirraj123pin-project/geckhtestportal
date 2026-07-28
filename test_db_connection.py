"""
File: test_db_connection.py
Checks whether the values in .env are loading correctly
and whether a connection to MySQL can be established.

Run with: python test_db_connection.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("Values loaded from .env:")
print("=" * 50)
print(f"MYSQL_HOST     = {os.getenv('MYSQL_HOST')}")
print(f"MYSQL_USER     = {os.getenv('MYSQL_USER')}")
print(f"MYSQL_PASSWORD = {os.getenv('MYSQL_PASSWORD')}")
print(f"MYSQL_DB       = {os.getenv('MYSQL_DB')}")
print("=" * 50)

# Now try an actual connection
try:
    import MySQLdb
    conn = MySQLdb.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        passwd=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DB')
    )
    print("SUCCESS! Connected to MySQL.")
    conn.close()
except Exception as e:
    print("FAILED! The following error occurred:")
    print(e)
    print("\nThis means the password or database name in .env is incorrect,")
    print("or the database has not been created yet (run database/schema.sql).")
