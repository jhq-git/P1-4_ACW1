// Renders the extracted or embedded payload fields.

import { card, createElement, keyValueList, sectionLabel } from "./dom.js";
import { formatTimestamp } from "./format.js";

const EMPTY_NOTE_TEXT = "No secret note.";
const EMPTY_SENDER_TEXT = "—";

/**
 * @param payload     PayloadView from the API
 * @param verified    true / false shows a tag; null hides it (Protect tab)
 * @param signatureHex optional signature to display
 */
export function renderPayloadCard({ payload, verified = null, signatureHex = null, title = "Payload" }) {
  const header = createElement("div", { className: "card__header" }, [
    createElement("h3", { className: "card__subtitle", text: title }, verified === null ? [] : [verificationTag(verified)]),
  ]);
  return card([
    header,
    sectionLabel("Secret note"),
    noteBox(payload.note),
    sectionLabel("Fields"),
    keyValueList(payloadRows(payload, signatureHex)),
  ]);
}

function payloadRows(payload, signatureHex) {
  const rows = [
    ["Sender", payload.sender_name || EMPTY_SENDER_TEXT],
    ["Media type", payload.media_type],
    ["Media ID", mono(payload.media_id)],
    ["Timestamp", formatTimestamp(payload.timestamp_iso)],
    ["Nonce", mono(payload.nonce_hex)],
    ["Media hash (SHA-256)", mono(payload.media_hash_hex)],
  ];
  if (signatureHex) rows.push(["Signature (Ed25519)", mono(signatureHex)]);
  return rows;
}

function noteBox(note) {
  const isEmpty = note.length === 0;
  return createElement("div", {
    className: isEmpty ? "note-box note-box--empty" : "note-box",
    text: isEmpty ? EMPTY_NOTE_TEXT : note,
  });
}

function verificationTag(verified) {
  return createElement("span", {
    className: verified ? "tag tag--verified" : "tag tag--unverified",
    text: verified ? "Verified" : "Unverified — do not trust",
  });
}

function mono(text) {
  return createElement("span", { className: "mono", text, title: text });
}

