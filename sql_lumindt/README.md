
````markdown
## Lumindt SQL Data Upload Tool
This tool allows Lumindt engineers to easily create PostgreSQL tables and insert test or measurement data into the shared Lumindt database server at **`10.1.10.12`**.


## ⚙️ Setup Instructions

### 1️⃣ Connect to the Network
- Ensure your computer is **connected to the Lumindt internal network via Ethernet**.  
- This is required to reach the PostgreSQL server.

### 2️⃣ Test Server Connection
Before proceeding, verify that your machine can reach the database server.

**Windows (Command Prompt):**
```bash
ping 10.1.10.12
````

**Mac/Linux (Terminal):**

```bash
ping -c 4 10.1.10.12
```

✅ You should see replies like:

```
Reply from 10.1.10.12: bytes=32 time<1ms TTL=64
```

If the request times out, ensure:

* You’re plugged into Ethernet
* The network adapter is enabled
* Firewall or VPN is not blocking internal traffic

---

## 💾 Installation

### Requirements

* Python 3.9 or higher
* PostgreSQL client library (`psycopg2`)

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

---

## 🧱 File Overview

| File                | Purpose                                                |
| ------------------- | ------------------------------------------------------ |
| `schema.sql`        | Defines the database table structure                   |
| `create.py`         | Creates or verifies the table on the server            |
| `insert_sql_row.py` | Contains the `insert_row()` function for adding data   |
| `example_insert.py` | Demonstrates how to import and use the insert function |
| `README.md`         | This documentation file                                |

---

## 🚀 Usage

### 🏗️ Create a Table

1. Open **`schema.sql`** and define your table structure.
   Example:

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

✅ Output:

```
Table created or verified successfully from schema.sql
```

---

### 📥 Insert Data (via Script)

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

Then run:

```bash
python your_script.py
```

✅ Output:

```
Inserted row into 'test_table' (5 fields)
```

---

### 🧪 Example Quick Test

You can also use the included example file:

```bash
python example_insert.py
```

This automatically generates random test data and uploads it to the database.

---

## 🧠 Troubleshooting

| Problem                                                    | Cause                                             | Solution                                            |
| ---------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------- |
| `connection timed out`                                     | Network not connected to internal Lumindt network | Connect via Ethernet, verify ping to 10.1.10.12     |
| `relation "test_table" does not exist`                     | Table not created yet                             | Run `python create.py` first                        |
| `psycopg2.errors.UndefinedColumn`                          | Column name mismatch                              | Ensure your dict keys match table column names      |
| `AttributeError: module 'psycopg2' has no attribute 'sql'` | Missing import                                    | Ensure `from psycopg2 import sql` is in your script |

---

## 👩‍🔧 Support

If you continue to have issues connecting or inserting data:

* Confirm that you are on the Lumindt internal network
* Contact the systems team for PostgreSQL server access verification
* Or reach out to **@kyle** on Slack

```

---

✅ Just copy this entire block, paste it into a file named **`README.md`**, and you’re done.  
It’s fully Markdown-formatted and ready for GitHub, GitLab, or internal documentation.
```
