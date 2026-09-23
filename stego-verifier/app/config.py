"""Application-wide constants.

Every protocol value lives here so the embedding format is defined in one place.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

# --- Byte encoding -----------------------------------------------------------
BYTE_ORDER = "big"
BITS_PER_BYTE = 8
TEXT_ENCODING = "utf-8"

# --- Location key derivation (scrypt) ----------------------------------------
KDF_SALT = b"P1-4_ACW1"
SCRYPT_COST = 2**14
SCRYPT_BLOCK_SIZE = 8
SCRYPT_PARALLELISM = 1
LOCATION_KEY_BYTES = 32
MIN_SECRET_KEY_LENGTH = 12

# --- Start location and keystream (HMAC-SHA256) ------------------------------
START_LABEL = b"start"
KEYSTREAM_LABEL = b"keystream"
START_DIGEST_BYTES = 8
KEYSTREAM_COUNTER_BYTES = 4

# --- LSB settings ------------------------------------------------------------
MIN_LSB_COUNT = 1
MAX_LSB_COUNT = 8
HEADER_LSB_COUNT = 1

# --- Header: magic (4 B) | lsb_count (1 B) | body_length (2 B) ---------------
MAGIC = b"STGO"
HEADER_STRUCT_FORMAT = ">4sBH"
HEADER_BYTES = 7
HEADER_SLOTS = HEADER_BYTES * BITS_PER_BYTE // HEADER_LSB_COUNT

# --- Body -------------------------------------------------------------------
PAYLOAD_VERSION = 1
# version (1) | media_type (1) | media_id (16) | timestamp_ms (8) | nonce (16) | media_hash (32)
BODY_FIXED_STRUCT_FORMAT = ">BB16sQ16s32s"
MEDIA_ID_BYTES = 16
NONCE_BYTES = 16
MEDIA_HASH_BYTES = 32
SENDER_LENGTH_BYTES = 1
NOTE_LENGTH_BYTES = 2
MAX_SENDER_BYTES = 64
MAX_NOTE_BYTES = 1024
SIGNATURE_BYTES = 64

# --- Media ------------------------------------------------------------------
IMAGE_EXTENSION = ".png"
AUDIO_EXTENSION = ".wav"
IMAGE_MIME_TYPE = "image/png"
AUDIO_MIME_TYPE = "audio/wav"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
WAV_RIFF_TAG = b"RIFF"
WAV_WAVE_TAG = b"WAVE"
WAV_WAVE_TAG_OFFSET = 8
SUPPORTED_AUDIO_SAMPLE_WIDTH_BYTES = 2
SUPPORTED_AUDIO_CHANNEL_COUNTS = (1, 2)
MAX_UPLOAD_BYTES = 64 * 1024 * 1024

# --- Visuals -----------------------------------------------------------------
MAX_PIXEL_VALUE = 255
WAVEFORM_BUCKET_COUNT = 1200
WAVEFORM_ZOOM_SAMPLE_COUNT = 400
METRIC_DECIMALS = 6

# --- Stego output naming -------------------------------------------------------
STEGO_FILENAME_SUFFIX = "_stego"

# --- Time --------------------------------------------------------------------
MILLISECONDS_PER_SECOND = 1000
