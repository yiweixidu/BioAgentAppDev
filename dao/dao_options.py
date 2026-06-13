# dao/dao_options.py
from dao.db_connection import get_connection


class OptionsDAO:

    def get_by_category(self, category: str):
        """Return list of values for a given category."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT value FROM app_options "
                    "WHERE category=%s ORDER BY value",
                    (category,))
                rows = cur.fetchall()
        return [r["value"] for r in rows]

    def add(self, category: str, value: str):
        """Add a new option (ignore if already exists)."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT IGNORE INTO app_options (category, value) "
                    "VALUES (%s, %s)",
                    (category, value))
            conn.commit()

    def delete(self, category: str, value: str):
        """Delete an option."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM app_options "
                    "WHERE category=%s AND value=%s",
                    (category, value))
            conn.commit()