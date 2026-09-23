// Shared front-end constants.

export const API = Object.freeze({
  KEYS: "/api/keys",
  LIMITS: "/api/limits",
  INSPECT: "/api/inspect",
  PROTECT: "/api/protect",
  VERIFY: "/api/verify",
  COMPARE: "/api/compare",
});

export const KEY_FILENAMES = Object.freeze({
  PRIVATE: "private.pem",
  PUBLIC: "public.pem",
});

export const PEM_MIME_TYPE = "application/x-pem-file";
export const PNG_MIME_TYPE = "image/png";

export const MEDIA_KIND = Object.freeze({ IMAGE: "image", AUDIO: "audio" });

export const BITS_PER_BYTE = 8;
export const PERCENT = 100;

export const VERDICT_STYLES = Object.freeze({
  "Authentic": { modifier: "authentic", icon: "✓" },
  "Tampered": { modifier: "tampered", icon: "!" },
  "Signature Invalid": { modifier: "signature-invalid", icon: "✕" },
  "Payload Missing": { modifier: "payload-missing", icon: "?" },
  "Cannot Verify": { modifier: "cannot-verify", icon: "–" },
});

export const CHECK_ICONS = Object.freeze({ passed: "✓", failed: "✕", skipped: "–" });

