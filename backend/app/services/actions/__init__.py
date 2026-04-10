"""Action handlers — one module per action kind.

Each handler module defines:
  - a Pydantic input schema (validated by the action bus)
  - an async handler function
  - registers itself via init_registry.py at app startup

This package is intentionally small — handlers are the *only* place where
direct ORM writes are allowed once the migration is complete. The NASA
linter will eventually enforce that rule.
"""
