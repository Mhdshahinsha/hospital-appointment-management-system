import psycopg2

def get_connection():

    conn = psycopg2.connect(
        host="/tmp",
        database="hospital_db",
        user="postgres"
    )

    return conn
