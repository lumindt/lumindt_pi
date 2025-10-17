

# Lumindt SQL Data Upload Tool

This tool allows Lumindt engineers to easily create PostgreSQL tables and insert test or measurement data into the shared Lumindt database server at `10.1.10.12`.

## Setup Instructions

### 1. Connect to the Network

* Ensure your computer is connected to the Lumindt internal network via Ethernet.
* This is required to reach the PostgreSQL server.

### 2. Test Server Connection

Before proceeding, verify that your machine can reach the database server.

**Windows (Command Prompt):**

```bash
ping 10.1.10.12
```

**Mac/Linux (Terminal):**

```bash
ping -c 4 10.1.10.12
```

You should see replies like:

```
Reply from 10.1.10.12: bytes=32 time<1ms TTL=64
```

If the request times out, ensure:

* You’re plugged into Ethernet
* The network adapter is enabled
* Firewall or VPN is not blocking internal traffic

## Installation

### Requirements

* Python 3.9 or higher
* PostgreSQL client library (`psycopg2`)
* Optional: DBeaver Community Edition (for viewing database tables)

### Step 1: Clone or Download This Repository

```bash
git clone https://github.com/Lumindt/sql_lumindt.git
cd sql_lumindt
```

Or copy this folder from another machine.

### Step 2: Install Dependencies

```bash
pip install psycopg2
```


## File Overview

| File                | Purpose                                                |
| ------------------- | ------------------------------------------------------ |
| `schema.sql`        | Defines the database table structure                   |
| `create.py`         | Creates or verifies the table on the server            |
| `insert_sql_row.py` | Contains the `insert_row()` function for adding data   |
| `example_insert.py` | Demonstrates how to import and use the insert function |
| `README.md`         | This documentation file                                |


## Usage

### 1. Create a Table

1. Open `schema.sql` and define your table structure. Example:

   ```sql
   CREATE TABLE IF NOT EXISTS test_table (
       id SERIAL PRIMARY KEY,
       pi_id TEXT NOT NULL,
       test_id TEXT,
       voltage DOUBLE PRECISION,
       current DOUBLE PRECISION,
       pressure DOUBLE PRECISION,
       time TIMESTAMPTZ DEFAULT now()
   );
   ```

2. Run the create script:

   ```bash
   python create.py
   ```

Expected output:

```
Table created or verified successfully from schema.sql
```


### 2. Insert Data from a Script

Use the `insert_sql_row` module in your own Python script:

```python
from insert_sql_row import insert_row

data = {
    "pi_id": "raspi123",
    "test_id": "run_45",
    "voltage": 4.7,
    "current": 1.3,
    "pressure": 1.02
}

insert_row(data, table_name="test_table")
```

Then run your script:

```bash
python your_script.py
```

Expected output:

```
Inserted row into 'test_table' (5 fields)
```

### 3. Quick Test Example

You can also use the included example file to automatically insert random data:

```bash
python example_insert.py
```

This script generates random test data and uploads it to the database.


## Viewing Data in DBeaver

### 1. Install DBeaver

Download and install DBeaver Community Edition from the official website:
[https://dbeaver.io/download/](https://dbeaver.io/download/)

### 2. Create a New Database Connection

1. Open DBeaver.
2. Click **Database → New Database Connection**.
3. Select **PostgreSQL** and click **Next**.

### 3. Enter Connection Details

* **Host**: `10.1.10.12`
* **Port**: `5432`
* **Database**: `test_data`
* **Username**: `postgres`
* **Password**: `Lumindt2themoon`
* Leave all other settings as default.

Click **Test Connection** to verify connectivity.
If successful, click **Finish**.

### 4. View the Table

1. In the **Database Navigator** pane (left sidebar), expand:

   ```
   PostgreSQL → test_data → Schemas → public → Tables
   ```
2. Find your table (for example, `test_table` or `L1_5_measurements`).
3. Right-click the table and choose **View Data → All Rows**.
4. You can now browse, sort, or export the table data directly in DBeaver.

---

## Troubleshooting

| Problem                                                    | Cause                                             | Solution                                                           |
| ---------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------ |
| `connection timed out`                                     | Network not connected to internal Lumindt network | Connect via Ethernet and verify ping to 10.1.10.12                 |
| `relation "test_table" does not exist`                     | Table not created yet                             | Run `python create.py` first                                       |
| `psycopg2.errors.UndefinedColumn`                          | Column name mismatch                              | Ensure your dictionary keys match the table column names           |
| `AttributeError: module 'psycopg2' has no attribute 'sql'` | Missing import                                    | Ensure you have `from psycopg2 import sql` in your script          |
| DBeaver cannot connect                                     | Firewall, VPN, or wrong credentials               | Disable VPN, check credentials, and verify you can ping the server |

---


