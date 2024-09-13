"""Basic tests of if the DB works inside tests."""
import traceback

from sqlalchemy import select

from arxiv.db import models, Session


def test_tables_exist(classic_db_engine):
    with classic_db_engine.connect() as conn:
        res = conn.execute(select(models.TapirPolicyClass).limit(1))
        len(res.fetchall()) > 0 # would raise error if table did not exist.

def test_basic_load_db_and_app(app):
    @app.route("/get_policy_classes")
    def get_policy_classes():
        try:
            res = Session.query(models.TapirPolicyClass)
            return "\n".join([f"{row.class_id}: {row.name}" for row in res])
        except Exception as e:
            return f"{e}\n{traceback.format_exc()}"

    with app.test_client() as client:
        res = client.get("/get_policy_classes")
        assert "admin" in res.text.lower()
        assert "public" in res.text.lower()
        assert "legacy" in res.text.lower()