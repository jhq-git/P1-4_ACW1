// Protect tab: collect inputs, show live capacity, embed and display results.

import { API, BITS_PER_BYTE, PERCENT } from "./constants.js";
import { buildFormData, postForm } from "./api.js";
import { byId, card, createElement, hideError, replaceChildren, showError, statGrid, withBusyButton } from "./dom.js";
import { base64ToBlob, downloadBlob, formatNumber, formatPercent, utf8ByteLength } from "./format.js";
import { bindByteCounter, setMeta } from "./form-controls.js";
import { renderComparison } from "./comparison-view.js";
import { renderPayloadCard } from "./payload-view.js";

const OVER_CAPACITY_CLASS = "is-over";

export function initProtectTab(limits) {
  const elements = collectElements();
  const state = { limits, cover: null };

  elements.coverInput.addEventListener("change", () => inspectCover(elements, state));
  elements.lsbSlider.addEventListener("input", () => updateLsbDisplay(elements, state));
  [elements.sender, elements.note].forEach((input) => input.addEventListener("input", () => updateCapacity(elements, state)));
  elements.form.addEventListener("submit", (event) => submitProtect(event, elements, state));

  configureLimits(elements, limits);
}

function collectElements() {
  return {
    form: byId("protect-form"),
    coverInput: byId("protect-cover"),
    coverMeta: byId("protect-cover-meta"),
    privateKey: byId("protect-private-key"),
    secretKey: byId("protect-secret-key"),
    secretKeyHint: byId("protect-secret-key-hint"),
    sender: byId("protect-sender"),
    senderCounter: byId("protect-sender-counter"),
    note: byId("protect-note"),
    noteCounter: byId("protect-note-counter"),
    lsbSlider: byId("protect-lsb"),
    lsbValue: byId("protect-lsb-value"),
    capacity: byId("protect-capacity"),
    capacityText: byId("protect-capacity-text"),
    capacityFill: byId("protect-capacity-fill"),
    error: byId("protect-error"),
    submit: byId("protect-submit"),
    results: byId("protect-results"),
  };
}

function configureLimits(elements, limits) {
  elements.lsbSlider.min = String(limits.min_lsb_count);
  elements.lsbSlider.max = String(limits.max_lsb_count);
  elements.secretKeyHint.textContent = `At least ${limits.min_secret_key_length} characters.`;
  bindByteCounter(elements.sender, elements.senderCounter, limits.max_sender_bytes);
  bindByteCounter(elements.note, elements.noteCounter, limits.max_note_bytes);
}

// --- Capacity ------------------------------------------------------------------

async function inspectCover(elements, state) {
  state.cover = null;
  const file = elements.coverInput.files[0];
  if (!file) return updateCapacity(elements, state);
  setMeta(elements.coverMeta, "Reading file…");
  try {
    state.cover = await postForm(API.INSPECT, buildFormData({ file }));
    setMeta(elements.coverMeta, `${state.cover.media_description} · ${formatNumber(state.cover.slot_count)} slots`);
  } catch (error) {
    setMeta(elements.coverMeta, error.message, true);
  }
  updateCapacity(elements, state);
}

function updateLsbDisplay(elements, state) {
  elements.lsbValue.textContent = elements.lsbSlider.value;
  updateCapacity(elements, state);
}

function requiredSlots(elements, limits) {
  const lsbCount = Number(elements.lsbSlider.value);
  const bodyBytes = limits.min_body_bytes + utf8ByteLength(elements.sender.value) + utf8ByteLength(elements.note.value);
  return limits.header_slots + Math.ceil((bodyBytes * BITS_PER_BYTE) / lsbCount);
}

function updateCapacity(elements, state) {
  const needed = requiredSlots(elements, state.limits);
  if (!state.cover) {
    elements.capacityText.textContent = `${formatNumber(needed)} slots needed · select a cover file`;
    elements.capacityFill.style.width = "0";
    elements.capacity.classList.remove(OVER_CAPACITY_CLASS);
    return;
  }
  const available = state.cover.slot_count;
  const ratio = Math.min(needed / available, 1);
  elements.capacityText.textContent = `${formatNumber(needed)} / ${formatNumber(available)} slots (${formatPercent(needed, available)})`;
  elements.capacityFill.style.width = `${ratio * PERCENT}%`;
  elements.capacity.classList.toggle(OVER_CAPACITY_CLASS, needed > available);
}

// --- Submit ----------------------------------------------------------------------

async function submitProtect(event, elements, state) {
  event.preventDefault();
  hideError(elements.error);
  const problem = findInputProblem(elements, state);
  if (problem) return showError(elements.error, problem);

  try {
    await withBusyButton(elements.submit, "Protecting…", () => protectAndRender(elements));
  } catch (error) {
    showError(elements.error, error.message);
  }
}

function findInputProblem(elements, state) {
  const { limits } = state;
  if (!elements.coverInput.files[0]) return "Choose a cover file.";
  if (!state.cover) return "The cover file could not be read. Choose a PNG or 16-bit WAV file.";
  if (!elements.privateKey.files[0]) return "Choose your private key (.pem).";
  if (elements.secretKey.value.length < limits.min_secret_key_length) {
    return `Secret key must be at least ${limits.min_secret_key_length} characters.`;
  }
  if (utf8ByteLength(elements.sender.value) > limits.max_sender_bytes) return "Sender is too long.";
  if (utf8ByteLength(elements.note.value) > limits.max_note_bytes) return "Secret note is too long.";
  if (requiredSlots(elements, limits) > state.cover.slot_count) {
    return "The payload does not fit. Increase k, shorten the note, or use a larger cover.";
  }
  return null;
}

async function protectAndRender(elements) {
  const coverFile = elements.coverInput.files[0];
  const result = await postForm(API.PROTECT, buildFormData({
    cover: coverFile,
    private_key: elements.privateKey.files[0],
    secret_key: elements.secretKey.value,
    lsb_count: elements.lsbSlider.value,
    sender_name: elements.sender.value,
    note: elements.note.value,
  }));
  const stegoBlob = base64ToBlob(result.stego_base64, result.mime_type);
  const comparison = await postForm(API.COMPARE, buildFormData({ original: coverFile, stego: stegoBlob }));
  replaceChildren(elements.results, [
    summaryCard(result, stegoBlob),
    renderComparison({ originalFile: coverFile, stegoBlob, comparison }),
    renderPayloadCard({ payload: result.payload, signatureHex: result.signature_hex, title: "Embedded payload" }),
  ]);
}

function summaryCard(result, stegoBlob) {
  const download = createElement("button", { className: "button button--primary", type: "button", text: `Download ${result.stego_filename}` });
  download.addEventListener("click", () => downloadBlob(stegoBlob, result.stego_filename));
  const usedSlots = result.header_slots + result.body_slots;
  return card([
    createElement("div", { className: "card__header" }, [
      createElement("div", {}, [
        createElement("h3", { className: "card__subtitle", text: "File protected" }),
        createElement("p", { className: "section-hint", text: result.media_description }),
      ]),
      download,
    ]),
    statGrid([
      ["Start slot (secret)", formatNumber(result.start_slot)],
      ["LSBs used (k)", String(result.lsb_count)],
      ["Slots used", `${formatNumber(usedSlots)} (${formatPercent(usedSlots, result.slot_count)})`],
      ["Payload size", `${formatNumber(result.body_length)} B`],
    ]),
  ]);
}
