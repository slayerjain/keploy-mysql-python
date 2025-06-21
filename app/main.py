import mysql.connector as mc
from flask import Flask, jsonify
import traceback
from itertools import islice

TARGET_ROWS = 100_000       # how many rows we want

DB_CFG = dict(
    host="127.0.0.1",
    port=3306,
    user="demo_user",
    password="demopass",
    database="demo",
    ssl_verify_cert=False,
    ssl_verify_identity=False,
    use_pure=True,
)

app = Flask(__name__)

# ------------------------------------------------------------------
def tls_cipher(conn):
    if hasattr(conn, "get_ssl_cipher"):
        return conn.get_ssl_cipher()
    cur = conn.cursor()
    cur.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
    row = cur.fetchone()
    cur.close()
    return row[1] if row else None

def ensure_lot_table_rows(cnx, want=TARGET_ROWS, chunk=1_000):
    """Insert rows until lot_table has `want` rows. Returns final count."""
    cur = cnx.cursor(buffered=True)
    cur.execute("SELECT COUNT(*) FROM lot_table")
    have = cur.fetchone()[0]
    cur.close()

    if have >= want:
        return have

    cur = cnx.cursor()
    next_id = have + 1
    while next_id <= want:
        batch_end = min(next_id + chunk - 1, want)
        rows = [(f"row_{i}",) for i in range(next_id, batch_end + 1)]
        cur.executemany("INSERT INTO lot_table (data) VALUES (%s)", rows)
        cnx.commit()
        next_id = batch_end + 1
    cur.close()
    return want

# ------------------------------------------------------------------
def run_db_checks():
    cnx = mc.connect(**DB_CFG)
    cur = cnx.cursor()
    cipher = tls_cipher(cnx)

    # 1. big-row aggregate (kept for multi-MiB traffic)
    cur.execute(
        "SELECT COUNT(*), ROUND(SUM(OCTET_LENGTH(data))/1048576, 2) "
        "FROM big_table WHERE id > 1"
    )
    count_big, total_big_mb = cur.fetchone()
    cur.close()

    # 2. make sure we **have** 100 000 rows, insert if needed
    final_rows = ensure_lot_table_rows(cnx)

    # 3. buffered cursor → pulls every packet immediately
    cur2 = cnx.cursor(buffered=True)
    cur2.execute("SELECT data FROM lot_table")
    _ = cur2.fetchall()          # discard but forces network read
    cur2.close()

    cnx.close()

    return {
        "tls_cipher": cipher,
        "big_rows": int(count_big),
        "big_rows_total_mib": float(total_big_mb),
        "lot_table_rows_streamed": final_rows,
        "status": "ok",
    }

# ------------------------------------------------------------------
@app.get("/run")
def run_handler():
    try:
        return jsonify(run_db_checks())
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(exc)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)