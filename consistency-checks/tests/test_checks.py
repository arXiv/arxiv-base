"""End-to-end checks against a SQLite DB and a local directory laid out like the bucket."""

import argparse
import gzip
import io
import shutil
import tarfile
import time
from pathlib import Path

import arxiv.legacy.papers.deleted as deleted_mod
import pytest
from sqlalchemy import create_engine, text

from consistency_checks.categories import Categories
from consistency_checks.checks import (
    categories_check,
    db_stats,
    deleted_papers,
    new_accounts,
    orig_consistency,
    recent_articles,
)
from consistency_checks.core import Context, Settings
from consistency_checks.papers import parse_key, parse_yymms

SCHEMA = """
CREATE TABLE tapir_users (user_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, joined_date INTEGER);
CREATE TABLE arXiv_demographics (user_id INTEGER PRIMARY KEY, affiliation TEXT);
CREATE TABLE tapir_nicknames (user_id INTEGER, nickname TEXT);
CREATE TABLE arXiv_paper_owners (user_id INTEGER, document_id INTEGER);
CREATE TABLE arXiv_moderators (user_id INTEGER, archive TEXT, subject_class TEXT);
CREATE TABLE arXiv_author_ids (user_id INTEGER, author_id TEXT, updated DATETIME);
CREATE TABLE arXiv_documents (document_id INTEGER PRIMARY KEY, paper_id TEXT, dated INTEGER);
CREATE TABLE arXiv_in_category (document_id INTEGER, archive TEXT, subject_class TEXT, is_primary INTEGER);
CREATE TABLE arXiv_metadata (document_id INTEGER, paper_id TEXT, version INTEGER, is_current INTEGER,
  is_withdrawn INTEGER DEFAULT 0, abs_categories TEXT, source_flags TEXT, authors TEXT,
  created DATETIME, updated DATETIME);
"""

LICENSE = "http://creativecommons.org/licenses/by/4.0/"


def abs_text(pid: str, cats: str, versions: int = 1, license: str | None = LICENSE) -> str:
    dates = "\n".join(
        (
            f"Date: Fri, 1 Jan 2021 00:00:0{v} GMT   (10kb)"
            if v == 1
            else f"Date (revised v{v}): Fri, 1 Jan 2021 00:00:0{v} GMT   (10kb)"
        )
        for v in range(1, versions + 1)
    )
    lic = f"License: {license}\n" if license else ""
    return (
        f"------------------------------------------------------------------------------\n\\\\\n"
        f"arXiv:{pid}\nFrom: Jane Doe <jane@example.org>\n{dates}\n\n"
        f"Title: A title\nAuthors: Jane Doe (Somewhere)\nCategories: {cats}\n{lic}\\\\\n"
        f"  An abstract.\n\\\\\n"
    )


def gz(data: bytes) -> bytes:
    return gzip.compress(data)


def tar_gz(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


@pytest.fixture
def env(tmp_path, monkeypatch):
    data = tmp_path / "data"

    def put(key: str, content: bytes | str) -> Path:
        path = data / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("latin-1") if isinstance(content, str) else content)
        return path

    db = tmp_path / "db.sqlite"
    engine = create_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        for stmt in SCHEMA.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))

    def sql(stmt: str, **params):
        with engine.begin() as conn:
            conn.execute(text(stmt), params)

    monkeypatch.setattr(deleted_mod, "_deleted_data", {"1105.2364": "was a duplicate"})
    settings = Settings(env="TEST", db_url=f"sqlite:///{db}", local_data_dir=str(data), workers=4)
    ctx = Context(settings)
    return ctx, put, sql


def add_paper(sql, doc_id: int, pid: str, cats: str, versions: int = 1, withdrawn_current=False, dbcp=None):
    sql("INSERT INTO arXiv_documents VALUES (:d, :p, :t)", d=doc_id, p=pid, t=int(time.time()))
    for v in range(1, versions + 1):
        sql(
            "INSERT INTO arXiv_metadata (document_id, paper_id, version, is_current, is_withdrawn, "
            "abs_categories, authors, created, updated) VALUES (:d, :p, :v, :c, :w, :a, 'X', "
            "datetime('now'), datetime('now'))",
            d=doc_id,
            p=pid,
            v=v,
            c=int(v == versions),
            w=int(withdrawn_current and v == versions),
            a=dbcp if dbcp is not None else cats,
        )
    primary, *secs = cats.split()
    for i, cat in enumerate([primary, *secs]):
        a, _, sc = cat.partition(".")
        sql("INSERT INTO arXiv_in_category VALUES (:d, :a, :s, :p)", d=doc_id, a=a, s=sc, p=int(i == 0))


def ns(**kw) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def test_categories_model():
    c = Categories("cs.SY")
    assert c.canonicalize() > 0 and str(c) == "eess.SY cs.SY"
    c = Categories("eess.SY cs.SY")
    assert c.canonicalize() == 0
    assert Categories("math.NA cs.NA").is_valid_for_id("1809.05446")
    assert not Categories("math.NA").is_valid_for_id("1809.05446")  # alias partner missing
    assert not Categories("cs.NA math.NA").is_valid_for_id("1809.05446")  # alias as primary
    assert Categories("astro-ph").is_valid_for_id("astro-ph/0101001")  # legacy until 2008-12
    assert not Categories("astro-ph").is_valid_for_id("0901.0001")
    assert not Categories("hep-ph").is_valid_for_id("hep-th/9901001")  # archive mismatch
    assert Categories("math-ph math.MP").is_valid_for_id("physics/9611002")  # KNOWN_BAD_PRIMARY
    assert not Categories("math-ph math.MP").is_valid_for_id("physics/9611003")
    assert Categories("funct-an math.FA").is_valid_for_id("funct-an/9501001")
    assert not Categories("funct-an math.FA").is_valid_for_id("funct-an/9205003")  # must be math.OA


def test_keys_and_months():
    assert (k := parse_key("orig/arxiv/papers/2101/2101.11864v2.tar.gz")) and k.version == 2
    assert (k := parse_key("ftp/hep-th/papers/9901/9901001.abs")) and k.paper_id == "hep-th/9901001"
    assert parse_key("ftp/arxiv/papers/2101/junk.txt") is None
    assert parse_yymms("9912-0002") == ["9912", "0001", "0002"]


def test_new_accounts(env, tmp_path):
    ctx, _put, sql = env
    flags = tmp_path / "FLAGS"
    flags.write_text("# known troublemaker\nEvil && Corp\n\n# other\nnomatch\n")
    now = int(time.time())
    for uid, nick, last, aff in ((1, "good", "Doe", "Uni"), (2, "bad", "Evil", "Corp Inc")):
        sql("INSERT INTO tapir_users VALUES (:u, 'A', :l, 'a@b', :t)", u=uid, l=last, t=now)
        sql("INSERT INTO arXiv_demographics VALUES (:u, :a)", u=uid, a=aff)
        sql("INSERT INTO tapir_nicknames VALUES (:u, :n)", u=uid, n=nick)
    r = new_accounts.run(ctx, ns(hours=24, flags_file=str(flags)))
    assert r.problems == 1
    assert "new account bad (2," in r.body and "found 'Evil && Corp', perhaps known troublemaker" in r.body
    r = new_accounts.run(ctx, ns(hours=24, flags_file=str(tmp_path / "missing")))
    assert r.problems == 0 and "nothing" in r.body


def test_db_stats(env):
    ctx, _put, sql = env
    add_paper(sql, 1, "2101.00001", "math.NA cs.NA")
    sql("INSERT INTO arXiv_moderators VALUES (1, 'math', 'NA')")
    r = db_stats.run(ctx, ns(days=7, no_search_counts=True))
    assert r.always_send and "Articles" in r.body and "Moderation gaps" in r.body
    assert "math.NA (" not in r.body.split("Moderation gaps")[1]  # has a moderator
    assert "math.AG (0)" in r.body


def test_deleted_papers(env):
    ctx, put, sql = env
    put("ftp/arxiv/papers/1105/1105.2364.abs", "")
    put("ftp/arxiv/papers/1105/1105.2364.tar.gz", b"x")
    sql("INSERT INTO arXiv_documents VALUES (9, '1105.2364', 0)")
    r = deleted_papers.run(ctx, ns())
    assert r.problems == 2
    assert "tar.gz" in r.body and "unexpected matching row (1) in arXiv_documents" in r.body


def test_recent_articles(env):
    ctx, put, sql = env
    add_paper(sql, 1, "2101.00001", "math.NA cs.NA", versions=2)
    put("ftp/arxiv/papers/2101/2101.00001.abs", abs_text("2101.00001", "math.NA cs.NA", versions=2))
    put("ftp/arxiv/papers/2101/2101.00001.tar.gz", tar_gz({"main.tex": b"hi"}))
    put("orig/arxiv/papers/2101/2101.00001v1.abs", abs_text("2101.00001", "cs.SY", license=None))
    put("orig/arxiv/papers/2101/2101.00001v1.gz", gz(b"hi")[:-6])  # truncated
    r = recent_articles.run(ctx, ns(days=1))
    assert "Found 4 files" in r.body
    assert "BAD FILE: orig/arxiv/papers/2101/2101.00001v1.gz" in r.body
    assert "NON CANONICAL Categories: orig/arxiv/papers/2101/2101.00001v1.abs" in r.body
    assert "Missing License in orig/arxiv/papers/2101/2101.00001v1.abs" in r.body
    assert r.problems == 3


def test_orig_consistency(env):
    ctx, put, sql = env
    add_paper(sql, 1, "2101.00001", "math.NA cs.NA", versions=2)
    add_paper(sql, 2, "2101.00002", "hep-th", withdrawn_current=True)
    put("ftp/arxiv/papers/2101/2101.00001.abs", "a")
    put("ftp/arxiv/papers/2101/2101.00001.gz", "a")
    put("orig/arxiv/papers/2101/2101.00001v1.abs", "a")  # v1 source missing
    put("ftp/arxiv/papers/2101/2101.00002.abs", "a")  # withdrawn: abs is enough
    put("ftp/arxiv/papers/2101/2101.00003.abs", "a")  # not in DB
    put("orig/arxiv/papers/2101/notes.txt", "a")
    put("orig/arxiv-sync.txt", "a")  # ignored
    put("orig/arxiv/stray", "a")
    r = orig_consistency.run(ctx, ns(yymm="2101"))
    assert "2101.00001v1 (orig): bad number of files: 1 (abs)" in r.body
    assert "2101.00003: unexpected files in ftp (no DB record)" in r.body
    assert "BAD FILE: orig/arxiv/papers/2101/notes.txt" in r.body
    assert "BAD FILE: orig/arxiv/stray" in r.body
    assert "2101.00002" not in r.body and "arxiv-sync" not in r.body
    assert r.problems == 4


def test_categories_check(env):
    ctx, put, sql = env
    add_paper(sql, 1, "2101.00001", "math.NA cs.NA")  # all good
    add_paper(sql, 2, "2101.00002", "math.NA", dbcp="math.NA")  # abs has alias partner, db not
    add_paper(sql, 3, "2101.00003", "hep-th", dbcp="hep-ph")  # dbcp disagrees
    put("ftp/arxiv/papers/2101/2101.00001.abs", abs_text("2101.00001", "math.NA cs.NA"))
    put("ftp/arxiv/papers/2101/2101.00002.abs", abs_text("2101.00002", "math.NA cs.NA"))
    put("ftp/arxiv/papers/2101/2101.00003.abs", abs_text("2101.00003", "hep-th"))
    r = categories_check.run(ctx, ns(yymm="2101"))
    assert "2101.00001" not in r.body
    assert "2101.00002: MISMATCH IN ALIASES ONLY: abs: math.NA cs.NA db: math.NA" in r.body
    assert "2101.00003: WARNING, db and abs match but dbcp bad" in r.body
    assert "Looked at 3 items, 2 warnings." in r.body


def test_main_and_mail(env, monkeypatch, capsys):
    ctx, put, _sql = env
    put("ftp/arxiv/papers/1105/1105.2364.abs", "")
    put("ftp/arxiv/papers/1105/1105.2364.gz", b"x")
    for key, value in (
        ("DB_URL", ctx.settings.db_url),
        ("LOCAL_DATA_DIR", ctx.settings.local_data_dir),
        ("ENV", "TEST"),
        ("MAIL_DRY_RUN", "false"),
        ("SMTP_URI", "smtps://u%40x:p%2Fw@smtp.test:465"),
    ):
        monkeypatch.setenv(key, value)
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent.append(("connect", host, port))

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def login(self, user, password):
            sent.append(("login", user, password))

        def send_message(self, msg):
            sent.append(("send", msg["To"], msg["Subject"], msg.get_content()))

    monkeypatch.setattr("smtplib.SMTP_SSL", FakeSMTP)
    from consistency_checks.__main__ import main

    assert main(["deleted_papers"]) == 0  # clean: no mail
    assert sent == [] and "Checked 1 deleted papers, 0 warnings." in capsys.readouterr().out
    assert main(["deleted_papers", "-v", "--mail-to", "ops@example.org"]) == 0
    assert sent[:2] == [("connect", "smtp.test", 465), ("login", "u@x", "p/w")]
    assert sent[2][:3] == ("send", "ops@example.org", "Deleted papers check")


def test_search_counts(monkeypatch):
    monkeypatch.setenv("GOOGLE_SEARCH_API_KEY", "k")
    monkeypatch.setenv("BING_API_KEY", "k")
    monkeypatch.setenv("SEARCH_INDEX_HOSTS", "arxiv.org,old.example.org")

    def fake_get_json(url):
        if "old.example.org" in url:
            raise OSError("HTTP Error 403")
        if "bing" in url:
            return {"d": [{"InIndex": 1}, {"InIndex": 42}]}
        return {"queries": {"request": [{"totalResults": "123"}]}}

    monkeypatch.setattr(db_stats, "_get_json", fake_get_json)
    google = "\n".join(db_stats.google_counts())
    assert "arxiv.org 123" in google and "old.example.org (failed to query google: HTTP Error 403)" in google
    assert "arxiv.org 42" in "\n".join(db_stats.bing_counts())
    monkeypatch.delenv("BING_API_KEY")
    assert "(skipped: BING_API_KEY not set)" in db_stats.bing_counts()


@pytest.mark.skipif(not shutil.which("pdfinfo"), reason="needs poppler-utils")
def test_pdf_check(env):
    ctx, put, _sql = env
    put("ftp/arxiv/papers/2101/2101.00009.pdf", b"%PDF-1.4 not really a pdf")
    [problem] = recent_articles.check_object(ctx.store, ctx.store.get("ftp/arxiv/papers/2101/2101.00009.pdf"))
    assert problem.startswith("BAD FILE: ftp/arxiv/papers/2101/2101.00009.pdf")
