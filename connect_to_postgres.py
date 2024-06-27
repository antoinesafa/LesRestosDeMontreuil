import psycopg2
from psycopg2 import OperationalError
from psycopg2 import extras
import traceback

def create_connection(db_name, db_user, db_password, db_host, db_port):
    print("db_name",db_name,"db_user",db_user,"db_password",db_password,"db_host",db_host,"port",db_port)
    connection_params = {
        'dbname': db_name,
        'user': db_user,
        'password': db_password,
        'host': db_host,
        'port': db_port,
        'cursor_factory': extras.DictCursor
    }
    try:
        conn = psycopg2.connect(**connection_params)
    except Exception as e:
        print(f"Exception: {e}")
    return conn

def execute_query(connection, query):
    if connection is None:
        print("Query to the database failed")
        return
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"OperationalError: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()

# Remplace les valeurs par celles correspondant à ta configuration PostgreSQL
connection = create_connection(
    "postgres",  # nom de ta base de données
    "postgres",  # ton nom d'utilisateur
    "portugal2.1",  # ton mot de passe
    "127.0.0.1",  # adresse de ton serveur PostgreSQL
    "5432")  # port de ton serveur PostgreSQL

print(connection)



# Exemple de requête pour vérifier la connexion
execute_query(connection, "SELECT version();")
import psycopg2
import random

def get_random_resto():
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(
            dbname="your_db_name",
            user="your_db_user",
            password="your_db_password",
            host="your_db_host",
            port="your_db_port"
        )

        # Create a cursor object
        cursor = conn.cursor()

        # Execute a query to get all restos
        cursor.execute("SELECT * FROM resto")

        # Fetch all rows from the executed query
        restos = cursor.fetchall()

        # Select a random resto
        if restos:
            random_resto = random.choice(restos)
            return random_resto
        else:
            return None

    except psycopg2.Error as e:
        print("Error while connecting to PostgreSQL", e)
    finally:
        # Close the database connection
        if conn:
            cursor.close()
            conn.close()

# Example usage
resto = get_random_resto()
if resto:
    print("Randomly selected resto:", resto)
else:
    print("No restos found")
