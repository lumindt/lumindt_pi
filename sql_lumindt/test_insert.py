from insert_sql_row import insert_row
import random

data = {
    "pi_id": 12345,
    "test_id": "curr_test",
    "voltage": random.uniform(1.0, 5.0),
    "current": random.uniform(0.1, 2.0),
    "pressure": random.uniform(0.8, 1.5)
}

insert_row(data, table_name="test_table")
