"""Opt-in PostgreSQL integration test; uses only a unique disposable schema."""
import os
import uuid

import pytest
from sqlalchemy import event, text

from src.ontology.authority_store import AuthorityStore
from src.graphstudio_sync.database import control_engine
from src.graphstudio_sync.config import SyncSettings


@pytest.mark.skipif(os.getenv("RUN_AUTHORITY_POSTGRES_TEST") != "1", reason="explicit integration run only")
def test_proposals_idempotent_and_revisions_transactional():
    from dotenv import load_dotenv
    load_dotenv(".env")
    engine = control_engine(SyncSettings.from_env())
    schema = "authority_test_" + uuid.uuid4().hex
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    def rewrite(conn, cursor, statement, parameters, context, executemany):
        return statement.replace("graphsync.", schema + "."), parameters
    event.listen(engine, "before_cursor_execute", rewrite, retval=True)
    try:
        store = AuthorityStore(engine)
        store.initialize()
        payload = {"classes": [{"className": "Example", "properties": []}], "relationships": []}
        first = store.stage(payload)
        assert store.stage(payload)["proposalId"] == first["proposalId"]
        assert len(store.snapshot()[1]) == 1
        plan = {"className": "Example", "revision": 0, "domain": "测试", "model": {"class": payload["classes"][0], "relationships": []}}
        with pytest.raises(RuntimeError):
            with engine.begin() as conn:
                store.save(conn, plan)
                raise RuntimeError("simulate failed transaction")
        assert store.snapshot()[0] == {}
        assert len(store.snapshot()[1]) == 1
        with engine.begin() as conn:
            store.save(conn, plan)
        authority, pending = store.snapshot()
        assert authority["Example"]["revision"] == 1
        assert pending == []
        assert store.stage(payload)["alreadyAccepted"] == 1
        plan["revision"] = 1
        with engine.begin() as conn:
            store.save(conn, plan)
        assert [h["revision"] for h in store.history("Example")] == [2, 1]
    finally:
        # schema is a generated, exclusively test-owned identifier; no business schema is touched.
        event.remove(engine, "before_cursor_execute", rewrite)
        with engine.begin() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        engine.dispose()
