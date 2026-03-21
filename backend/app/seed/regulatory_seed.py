"""Regulatory department seed data — ~200 neurons covering aerospace standards.

Run directly to populate an existing DB:
    cd backend && python -m app.seed.regulatory_seed
"""

import json
import re

import psycopg2

from app.tenant import tenant

DEPARTMENT = tenant.regulatory_department


def _cross_ref(depts: list[str]) -> str:
    return json.dumps(depts)


# Structure: list of (role_label, role_key, cross_ref_depts, standard_date, tasks)

REGULATORY_TREE = tenant.regulatory_tree



def _get_pg_dsn() -> str:
    """Get PostgreSQL connection string from environment or config defaults."""
    from app.config import settings
    url = settings.database_url
    # Convert asyncpg URL to psycopg2 format
    url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    return url


def seed_regulatory(force: bool = False):
    """Insert regulatory neurons into existing database.

    Args:
        force: If True, delete all existing Regulatory neurons and re-seed.
    """
    dsn = _get_pg_dsn()
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()

    # Ensure standard_date column exists
    cursor.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'neurons' AND column_name = 'standard_date'"
    )
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE neurons ADD COLUMN standard_date VARCHAR(20)")
        conn.commit()
        print("Migrated: added neurons.standard_date (sync)")

    # Check if Regulatory department already exists
    cursor.execute("SELECT COUNT(*) FROM neurons WHERE department = %s", (DEPARTMENT,))
    existing = cursor.fetchone()[0]

    if existing > 0 and not force:
        print(f"Regulatory department already has {existing} neurons — skipping")
        conn.close()
        return existing

    if existing > 0 and force:
        print(f"Force re-seed: deleting {existing} existing Regulatory neurons")
        cursor.execute("DELETE FROM neurons WHERE department = %s", (DEPARTMENT,))

    created = 0

    # L0: Department
    cursor.execute(
        "INSERT INTO neurons (layer, node_type, label, department, summary, created_at_query_count) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (0, "department", DEPARTMENT, DEPARTMENT, f"Department: {DEPARTMENT}", 0),
    )
    dept_id = cursor.fetchone()[0]
    created += 1

    for role_label, role_key, cross_ref_depts, standard_date, tasks in REGULATORY_TREE:
        # L1: Role (standard family)
        cursor.execute(
            "INSERT INTO neurons (parent_id, layer, node_type, label, role_key, department, summary, cross_ref_departments, standard_date, created_at_query_count) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (dept_id, 1, "role", role_label, role_key, DEPARTMENT,
             f"Role: {role_label} in {DEPARTMENT}",
             _cross_ref(cross_ref_depts), standard_date, 0),
        )
        role_id = cursor.fetchone()[0]
        created += 1

        for task_entry in tasks:
            task_label, task_summary, task_content, task_cross_ref, systems = task_entry
            cursor.execute(
                "INSERT INTO neurons (parent_id, layer, node_type, label, role_key, department, summary, content, cross_ref_departments, created_at_query_count) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (role_id, 2, "task", task_label, role_key, DEPARTMENT,
                 task_summary, task_content,
                 _cross_ref(task_cross_ref) if task_cross_ref else None, 0),
            )
            task_id = cursor.fetchone()[0]
            created += 1

            for sys_label, sys_summary, sys_content in systems:
                cursor.execute(
                    "INSERT INTO neurons (parent_id, layer, node_type, label, role_key, department, summary, content, created_at_query_count) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (task_id, 3, "system", sys_label, role_key, DEPARTMENT,
                     sys_summary, sys_content, 0),
                )
                created += 1

    conn.commit()
    conn.close()
    print(f"Seeded {created} regulatory neurons")
    return created


if __name__ == "__main__":
    seed_regulatory()
