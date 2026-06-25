def test_prerequisite_path_walks_predecessors(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_VAULT_DATABASE_URL", str(tmp_path / "test.db"))

    from importlib import reload

    import backend.app.database as db
    import backend.app.graph as graph

    reload(db)
    reload(graph)
    db.init_db()

    basics = db.upsert_concept("basics")
    algebra = db.upsert_concept("algebra")
    calculus = db.upsert_concept("calculus")

    db.insert_relationship(basics, algebra, "depends_on", 1.0, None)
    db.insert_relationship(algebra, calculus, "depends_on", 1.0, None)

    steps = graph.prerequisite_path(calculus, depth=3)

    assert [step["name"] for step in steps] == ["calculus", "algebra", "basics"]
