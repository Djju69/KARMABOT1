import os
import re
import secrets
import string

import psycopg2


def generate_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL is missing")

    odoo_pass = os.getenv("ODOO_DB_PASSWORD") or generate_password()

    conn = psycopg2.connect(db_url, sslmode="require")
    conn.autocommit = True
    cur = conn.cursor()

    sql = (
        """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'karmabot_odoo') THEN
    EXECUTE $$CREATE ROLE karmabot_odoo WITH LOGIN PASSWORD '%s' NOSUPERUSER NOCREATEROLE$$;
    EXECUTE $$ALTER ROLE karmabot_odoo CREATEDB$$;
  ELSE
    EXECUTE $$ALTER ROLE karmabot_odoo WITH PASSWORD '%s'$$;
    IF NOT EXISTS (
      SELECT 1 FROM pg_roles r JOIN pg_authid a ON r.rolname='karmabot_odoo' AND a.oid=r.oid AND a.rolcreatedb = true
    ) THEN
      EXECUTE $$ALTER ROLE karmabot_odoo CREATEDB$$;
    END IF;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'odoo') THEN
    EXECUTE $$CREATE DATABASE odoo OWNER karmabot_odoo ENCODING 'UTF8' TEMPLATE template0$$;
  END IF;
END$$;
"""
        % (odoo_pass, odoo_pass)
    )
    cur.execute(sql)
    cur.close()
    conn.close()

    # Extract host/port from DATABASE_URL for Odoo service config
    m = re.match(r"^postgres(?:ql)?://.*?@(.*?):(\d+)/(.*)$", db_url)
    if m:
        print("ODK_HOST:", m.group(1))
        print("ODK_PORT:", m.group(2))
    print("ODOO_DB_USER: karmabot_odoo")
    print("ODOO_DB_PASSWORD:", odoo_pass)
    print("ODOO_DATABASE: odoo")


if __name__ == "__main__":
    try:
        main()
        print("Done.")
    except Exception as e:
        print("ERROR:", e)
        raise


