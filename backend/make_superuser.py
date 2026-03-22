#!/usr/bin/env python3
"""Usage: python make_superuser.py user@example.com"""
import sys, os, psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:tennissuper369@localhost:5432/competitions_db")

if len(sys.argv) < 2:
    print("Usage: python make_superuser.py <email>")
    sys.exit(1)

email = sys.argv[1].strip().lower()
conn = psycopg2.connect(DATABASE_URL)
with conn.cursor() as cur:
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    row = cur.fetchone()
    if not row:
        print(f"Пользователь {email} не найден.")
        sys.exit(1)
    cur.execute("UPDATE users SET is_superuser=TRUE WHERE email=%s", (email,))
    conn.commit()
print(f"✅ {email} теперь суперпользователь.")
conn.close()
