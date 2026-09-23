"""HTTP API smoke tests."""

import base64

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import SECRET_KEY

client = TestClient(app)


def test_index_and_limits_are_served():
    assert client.get("/").status_code == 200
    limits = client.get("/api/limits").json()
    assert limits["header_slots"] == 56
    assert limits["min_body_bytes"] == 141


def test_protect_verify_compare_round_trip(covers):
    keys = client.post("/api/keys").json()
    protect_response = client.post(
        "/api/protect",
        files={"cover": ("cover.png", covers["png_rgb"]), "private_key": ("private.pem", keys["private_pem"])},
        data={"secret_key": SECRET_KEY, "lsb_count": "2", "sender_name": "Bob", "note": "hello"},
    )
    assert protect_response.status_code == 200, protect_response.text
    result = protect_response.json()
    assert result["stego_filename"] == "cover_stego.png"
    stego = base64.b64decode(result["stego_base64"])

    verify_response = client.post(
        "/api/verify",
        files={"stego": ("s.png", stego), "public_key": ("public.pem", keys["public_pem"])},
        data={"secret_key": SECRET_KEY},
    ).json()
    assert verify_response["verdict"] == "Authentic"
    assert verify_response["payload"]["note"] == "hello"

    comparison = client.post("/api/compare", files={"original": covers["png_rgb"], "stego": stego}).json()
    assert comparison["media_kind"] == "image"
    assert comparison["changed_values"] > 0


def test_audio_comparison(covers):
    keys = client.post("/api/keys").json()
    result = client.post(
        "/api/protect",
        files={"cover": ("a.wav", covers["wav_stereo"]), "private_key": ("p.pem", keys["private_pem"])},
        data={"secret_key": SECRET_KEY, "lsb_count": "4"},
    ).json()
    stego = base64.b64decode(result["stego_base64"])
    comparison = client.post("/api/compare", files={"original": covers["wav_stereo"], "stego": stego}).json()
    assert comparison["media_kind"] == "audio"
    assert len(comparison["zoom"]["original"]) > 0


def test_bad_input_returns_readable_error(covers):
    keys = client.post("/api/keys").json()
    response = client.post(
        "/api/protect",
        files={"cover": ("c.png", covers["png_rgb"]), "private_key": ("p.pem", keys["private_pem"])},
        data={"secret_key": "short", "lsb_count": "1"},
    )
    assert response.status_code == 400
    assert "at least" in response.json()["detail"]
