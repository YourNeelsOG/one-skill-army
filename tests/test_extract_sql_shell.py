"""Tests for SQL and shell extraction through the table engine."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors import extract_file
from osa.index import build_graph
from test_provenance import GraphCase


def kinds(result):
    return {n["id"]: n["kind"] for n in result["nodes"]}


class TestSql(GraphCase):
    def test_definitions_case_insensitive(self):
        src = ("create table if not exists Users (id int primary key);\n"
               "CREATE OR REPLACE VIEW active_users AS SELECT * FROM users;\n"
               "CREATE FUNCTION touch() RETURNS trigger AS 'x' LANGUAGE sql;\n"
               "CREATE INDEX idx_users_id ON users (id);\n"
               "CREATE TABLE \"public\".\"orders\" (\n"
               "  id int,\n  user_id int REFERENCES users(id)\n);\n")
        result = extract_file("db/schema.sql", src)
        k = kinds(result)
        self.assertEqual(k["db/schema.sql::users"], "table")
        self.assertEqual(k["db/schema.sql::active_users"], "view")
        self.assertEqual(k["db/schema.sql::touch"], "function")
        self.assertEqual(k["db/schema.sql::idx_users_id"], "index")
        self.assertEqual(k["db/schema.sql::orders"], "table")
        refs = {(e["source"], e.get("target")) for e in result["edges"]
                if e["rel"] == "references"}
        self.assertIn(("db/schema.sql::orders", "db/schema.sql::users"), refs)
        self.assertIn(("db/schema.sql::active_users", "db/schema.sql::users"),
                      refs)
        self.assertIn(("db/schema.sql::idx_users_id", "db/schema.sql::users"),
                      refs)

    def test_commented_sql_is_ignored(self):
        src = "-- CREATE TABLE ghost (id int);\n/* CREATE VIEW v AS x */\n"
        self.assertEqual([n["id"] for n in
                          extract_file("a.sql", src)["nodes"]], ["a.sql"])

    def test_foreign_key_across_migration_files_is_inferred(self):
        self.write("m/001.sql", "CREATE TABLE users (id int);\n")
        self.write("m/002.sql", "CREATE TABLE posts (\n"
                                "  user_id int REFERENCES users (id)\n);\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "m/002.sql::posts",
                                      "m/001.sql::users", "references",
                                      "INFERRED"))

    def test_statement_after_definition_is_not_attributed_to_it(self):
        src = ("CREATE TABLE a (id int);\n"
               "INSERT INTO a SELECT id FROM b_source;\n")
        result = extract_file("x.sql", src)
        sources = {e["source"] for e in result["edges"]
                   if e["rel"] == "references"}
        self.assertNotIn("x.sql::a", sources)


class TestShell(GraphCase):
    def test_functions(self):
        src = ("#!/usr/bin/env bash\n"
               "setup() {\n  echo hi\n}\n"
               "function cleanup {\n  rm -f x\n}\n"
               "# fake() { }\n")
        k = kinds(extract_file("run.sh", src))
        self.assertEqual(k["run.sh::setup"], "function")
        self.assertEqual(k["run.sh::cleanup"], "function")
        self.assertNotIn("run.sh::fake", k)

    def test_source_and_script_references(self):
        self.write("scripts/lib.sh", "helper() { :; }\n")
        self.write("scripts/deploy.sh", "echo deploy\n")
        self.write("scripts/install.sh",
                   'DIR="$(cd "$(dirname "$0")" && pwd)"\n'
                   'source "$DIR/lib.sh"\n'
                   'bash "$DIR/deploy.sh"\n'
                   '# source "$DIR/ghost.sh"\n')
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "scripts/install.sh",
                                      "scripts/lib.sh", "imports",
                                      "INFERRED"))
        self.assertTrue(self.has_edge(graph, "scripts/install.sh",
                                      "scripts/deploy.sh", "references",
                                      "INFERRED"))
        targets = {e["target"] for e in graph["edges"]}
        self.assertNotIn("scripts/ghost.sh", targets)
        # A sourced file is an import; the same path is not also a reference.
        self.assertFalse(self.has_edge(graph, "scripts/install.sh",
                                       "scripts/lib.sh", "references"))


if __name__ == "__main__":
    unittest.main()
