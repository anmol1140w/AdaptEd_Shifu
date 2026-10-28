from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.infrastructure.database import connection as database


class Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class BootstrapConnection:
    def __init__(self, has_version: bool):
        self.has_version = has_version
        self.executed: list[str] = []
        self.commits = 0

    def execute(self, query, _params=None):
        self.executed.append(query)
        if "SELECT version FROM adapted_schema_versions" in query:
            return Cursor({"version": database.DATABASE_SCHEMA_VERSION} if self.has_version else None)
        return Cursor()

    def commit(self):
        self.commits += 1


class DatabaseBootstrapTests(unittest.TestCase):
    def test_schema_runs_once_when_version_is_missing(self):
        connection = BootstrapConnection(has_version=False)

        with patch.object(database, "seed_granular_content"), patch.object(database, "seed_pcm_learning_content"):
            database._initialize_database(connection)  # type: ignore[arg-type]

        self.assertIn(database.SCHEMA, connection.executed)
        self.assertEqual(connection.commits, 1)
        self.assertIn("SELECT pg_advisory_xact_lock(%s)", connection.executed)

    def test_current_schema_version_skips_ddl_but_refreshes_seeds(self):
        connection = BootstrapConnection(has_version=True)
        granular = patch.object(database, "seed_granular_content")
        pcm = patch.object(database, "seed_pcm_learning_content")

        with granular as seed_granular, pcm as seed_pcm:
            database._initialize_database(connection)  # type: ignore[arg-type]

        self.assertNotIn(database.SCHEMA, connection.executed)
        seed_granular.assert_called_once_with(connection)
        seed_pcm.assert_called_once_with(connection)


if __name__ == "__main__":
    unittest.main()
