import psycopg2
from psycopg2 import sql

def insert_row(data: dict, table_name="L1_5_measurements"):
    """
    Inserts a row into the given table using key-value pairs. The keys in the dictionary must match the column names in the table. 
    Missing keys will be set to NULL.

    Args:
        data (dict): A dictionary where keys are column names and values are the corresponding values to insert.
        table_name (str): The name of the table to insert the data into. Default is "L1_5_measurements".

    Example:
        insert_row({
            "pi_id": "raspi123",
            "test_id": "run_45",
            "fc_voltage": 52.3,
            "el_output_pressure": 1.22
        })
    """

    conn = psycopg2.connect(dbname="test_data", user="postgres", password="Lumindt2themoon", host="10.1.10.12", port="5432")
    conn.autocommit = True
    cur = conn.cursor()

    # Dynamically build the INSERT statement
    columns = list(data.keys())
    values = [data[col] for col in columns]

    query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({placeholders});").format(
        table=sql.Identifier(table_name),
        fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
        placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )

    cur.execute(query, values)
    cur.close()
    conn.close()
    print(f"Inserted row into '{table_name}' ({len(columns)} fields)")
