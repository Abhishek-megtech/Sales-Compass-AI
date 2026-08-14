"""
Diagnostic script: check PostgreSQL server state and set up the
required user/database if needed.
"""
import sys
import psycopg2

# Step 1: Check if PostgreSQL is running at all
print("=== PostgreSQL Diagnostics ===\n")

# Try various known connection strings
attempts = [
    {"host": "localhost", "port": 5432, "dbname": "postgres", "user": "postgres", "label": "postgres/postgres (no pw)"},
    {"host": "localhost", "port": 5432, "dbname": "postgres", "user": "postgres", "password": "postgres", "label": "postgres/postgres (pw=postgres)"},
    {"host": "localhost", "port": 5432, "dbname": "postgres", "user": "postgres", "password": "admin", "label": "postgres/postgres (pw=admin)"},
]

connected_conn = None
for attempt in attempts:
    label = attempt.pop("label")
    try:
        conn = psycopg2.connect(**attempt)
        print(f"[PASS] Connected as: {label}")
        connected_conn = conn
        break
    except psycopg2.OperationalError as e:
        msg = str(e).split('\n')[0]
        print(f"[FAIL] {label}: {msg}")

if connected_conn is None:
    print("\nCould not connect to PostgreSQL as superuser.")
    print("Please ensure PostgreSQL is running and you know the superuser password.")
    sys.exit(1)

# Step 2: List existing users and databases
cur = connected_conn.cursor()
cur.execute("SELECT usename FROM pg_user ORDER BY usename;")
users = [r[0] for r in cur.fetchall()]
print(f"\nExisting users: {users}")

cur.execute("SELECT datname FROM pg_database ORDER BY datname;")
dbs = [r[0] for r in cur.fetchall()]
print(f"Existing databases: {dbs}")

# Step 3: Check if sales_user exists
user_exists = "sales_user" in users
db_exists = "sales_compass_ai" in dbs

print(f"\nsales_user exists: {user_exists}")
print(f"sales_compass_ai database exists: {db_exists}")

# Step 4: Create them if missing — need a fresh connection with autocommit
connected_conn.close()
# Re-open with autocommit (CREATE USER/DATABASE cannot run inside a transaction)
for attempt in [
    {"host": "localhost", "port": 5432, "dbname": "postgres", "user": "postgres", "password": "postgres"},
]:
    connected_conn = psycopg2.connect(**attempt)
    connected_conn.autocommit = True
    cur = connected_conn.cursor()
    break

if not user_exists:
    print("\nCreating user 'sales_user' with password 'jaga jassos'...")
    cur.execute("CREATE USER sales_user WITH PASSWORD 'jaga jassos';")
    print("[PASS] User created.")

if not db_exists:
    print("Creating database 'sales_compass_ai'...")
    cur.execute("CREATE DATABASE sales_compass_ai OWNER sales_user;")
    print("[PASS] Database created.")
else:
    print("Granting privileges on existing database...")
    cur.execute("GRANT ALL PRIVILEGES ON DATABASE sales_compass_ai TO sales_user;")
    print("[PASS] Privileges granted.")

# Step 5: Verify the sales_user can now connect
print("\nVerifying sales_user connection with original password...")
try:
    test_conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="sales_compass_ai",
        user="sales_user",
        password="jaga jassos"
    )
    print("[PASS] sales_user connected to sales_compass_ai!")
    test_conn.close()
except psycopg2.OperationalError as e:
    print(f"[FAIL] sales_user still cannot connect: {e}")

connected_conn.close()
print("\nDone.")
