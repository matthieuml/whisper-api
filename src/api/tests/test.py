import json
from io import BytesIO

import pytest

from api.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_root(client):
    rv = client.get("/")
    assert b"WHISPER API" in rv.data


def test_transcribe_get(client):
    rv = client.get("/transcribe")
    assert b"Upload a File" in rv.data


def test_transcribe_post_no_file(client):
    rv = client.post("/transcribe", data={}, follow_redirects=True)
    assert b"No file part!" in rv.data


def test_transcribe_post_empty_filename(client):
    rv = client.post(
        "/transcribe",
        data={"file": (BytesIO(b"my file contents"), "")},
        follow_redirects=True,
    )
    assert b"No file selected!" in rv.data


def test_transcribe_post_invalid_extension(client):
    rv = client.post(
        "/transcribe",
        data={"file": (BytesIO(b"my file contents"), "invalid-extension.txt")},
        follow_redirects=True,
    )
    assert b"File extension not allowed!" in rv.data


def test_transcribe_post_valid_file(client):
    rv = client.get("/result/random-id")
    data = json.loads(rv.data)
    assert data["ready"] is False
    assert data["successful"] is False
    assert data["value"] is None
