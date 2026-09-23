# P1-4 ACW1 — INF2005 Steganography Tool

Web-based LSB replacement steganography tool that protects PNG images and 16-bit WAV audio with an embedded, Ed25519-signed verification payload, then verifies them later.

## Quick start

```bash
cd stego-verifier
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

1. **Keys** tab → Generate key pair → download `private.pem` and `public.pem`.
2. **Protect** tab → choose a cover (try `samples/`), the private key, a secret key (≥ 12 chars), sender, secret note and k → Protect → download the stego file.
3. **Verify** tab → choose the stego file, the public key and the same secret key (optionally the original for comparison) → Verify.

Run the automated tests with `pytest`.

## How it works

| Step | Protect | Verify |
|---|---|---|
| Location key | `K = scrypt(secret_key, salt="P1-4_ACW1")` | same |
| Start slot | `S = HMAC(K, "start")[:8] mod N` | same |
| Keystream | `HMAC(K, "keystream" ‖ counter)` blocks | same |
| Hash | SHA-256 of all samples with the payload bits cleared | recompute and compare |
| Payload | header (`STGO`, k, body length) + signed body | read header → body → check signature |
| Embedding | header in LSB-1, body in k LSBs, sequential from S, XORed with keystream | reverse |

Verdicts (first failing check decides): **Cannot Verify** → **Payload Missing** → **Tampered** (header fields) → **Signature Invalid** → **Tampered** (hash) → **Authentic**.

The full design, including limitations for the report, is in the project's *ACW1 Design Spec*.

## Project layout

```
app/
  config.py            All protocol constants (magic, salt, sizes, limits)
  main.py              FastAPI app factory, static files, error handler
  core/                Pure logic — no HTTP, no file formats
    bits.py              bytes ↔ bits ↔ k-bit slot values (MSB first)
    location.py          scrypt key, start slot, XOR keystream
    payload.py           header/body binary layout and parsing
    layout.py            which slots hold header and body
    embedding.py         LSB write / read / clear on slot arrays
    hashing.py           media hash with payload bits cleared
    signing.py           Ed25519 generate / load / sign / verify
    errors.py            domain exceptions
  media/               File formats
    base.py              CoverMedia interface
    image_cover.py       PNG (L, LA, RGB, RGBA; palette → RGB, 1-bit → L)
    audio_cover.py       16-bit PCM WAV (mono / stereo)
    loader.py            detect type by signature
  services/            Workflows
    protector.py         Protect pipeline
    verifier.py          ordered checks → verdict
    payload_channel.py   encrypt + embed / read + decrypt
    verdicts.py          verdict enum and report model
    validation.py        user input checks
  visuals/             Comparison data (difference map, metrics, waveforms)
  api/                 HTTP layer (routes, schemas, presenters, uploads)
static/                index.html, css/styles.css, js/ (one module per concern)
tests/                 pytest: every verdict for image and audio + API smoke tests
samples/               demo covers (RGB PNG, greyscale PNG, stereo WAV)
```

## Manual demo checklist

| Scenario | How | Expected |
|---|---|---|
| Round trip, k = 1–8 | App | Authentic |
| Draw on image / silence part of audio | Paint / Audacity | Tampered |
| Wrong public key | Generate a second key pair | Signature Invalid |
| Flip a payload byte (WAV) | Hex editor | Signature Invalid |
| Wrong secret key / unprotected file | App | Payload Missing |
| Crop / trim | GIMP / Audacity | Payload Missing |
| Lossy round trip (JPEG, MP3) | Export and back | Payload Missing |
| JPEG, 24-bit WAV, corrupt file | App | Cannot Verify |
| Sample-rate header edit | Hex editor (WAV bytes 24–27) | Authentic (known limitation) |
