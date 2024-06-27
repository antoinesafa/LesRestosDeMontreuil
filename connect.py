import psycopg2
from config import load_config
from psycopg2 import extras

def connect(config):
    print("avant le try")
    conn = psycopg2.connect(**config)
    print('Connected to the postgresql server')
    print("conn",conn)
    return conn

if __name__ == '__main__':
    config = load_config()
    print("config", config)
    connected = connect(config)
    print("connected",connected)