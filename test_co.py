import psycopg2
from psycopg2 import OperationalError

try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="db_resto",
        user="postgres",
        password="portugal2.1",
        port="5432",
        connect_timeout=5
    )
    print("Connection successful")
except OperationalError as e:
    print(f"OperationalError: {e}")
    if e.pgcode:
        print(f"pgcode: {e.pgcode}")
    if e.pgerror:
        print(f"pgerror: {e.pgerror}")
    if e.diag:
        print(f"Details: {e.diag.message_primary}, {e.diag.message_detail}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")