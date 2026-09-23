// Verify tab: submit a stego file and render the verdict, checks and payload.

import { API, CHECK_ICONS, VERDICT_STYLES } from "./constants.js";
import { buildFormData, postForm } from "./api.js";
import { byId, card, createElement, hideError, keyValueList, replaceChildren, showError, withBusyButton } from "./dom.js";
import { formatOptionalNumber, orNotApplicable } from "./format.js";
import { setMeta } from "./form-controls.js";
import { renderComparison, renderPreview } from "./comparison-view.js";
import { renderPayloadCard } from "./payload-view.js";

export function initVerifyTab() {
  const elements = {
    form: byId("verify-form"),
    stegoInput: byId("verify-stego"),
    stegoMeta: byId("verify-stego-meta"),
    publicKey: byId("verify-public-key"),
    secretKey: byId("verify-secret-key"),
    original: byId("verify-original"),
    error: byId("verify-error"),
    submit: byId("verify-submit"),
    results: byId("verify-results"),
  };
  elements.stegoInput.addEventListener("change", () => describeStego(elements));
  elements.form.addEventListener("submit", (event) => submitVerify(event, elements));
}

async function describeStego(elements) {
  const file = elements.stegoInput.files[0];
  if (!file) return setMeta(elements.stegoMeta, "");
  try {
    const info = await postForm(API.INSPECT, buildFormData({ file }));
    setMeta(elements.stegoMeta, info.media_description);
  } catch (error) {
    setMeta(elements.stegoMeta, error.message, true);
  }
}

async function submitVerify(event, elements) {
  event.preventDefault();
  hideError(elements.error);
  const problem = findInputProblem(elements);
  if (problem) return showError(elements.error, problem);
  try {
    await withBusyButton(elements.submit, "Verifying…", () => verifyAndRender(elements));
  } catch (error) {
    showError(elements.error, error.message);
  }
}

function findInputProblem(elements) {
  if (!elements.stegoInput.files[0]) return "Choose the file to verify.";
  if (!elements.publicKey.files[0]) return "Choose the public key (.pem).";
  if (!elements.secretKey.value) return "Enter the secret key.";
  return null;
}

async function verifyAndRender(elements) {
  const stegoFile = elements.stegoInput.files[0];
  const report = await postForm(API.VERIFY, buildFormData({
    stego: stegoFile,
    public_key: elements.publicKey.files[0],
    secret_key: elements.secretKey.value,
  }));
  const cards = [verdictBanner(report), checklistCard(report)];
  if (report.payload) cards.push(renderPayloadCard({ payload: report.payload, verified: report.payload_verified, title: "Extracted payload" }));
  if (report.expected_hash_hex) cards.push(hashCard(report));
  const mediaCard = await buildMediaCard(elements.original.files[0], stegoFile, report.media_kind);
  if (mediaCard) cards.push(mediaCard);
  replaceChildren(elements.results, cards);
}

async function buildMediaCard(originalFile, stegoFile, mediaKind) {
  if (!mediaKind) return null;
  if (!originalFile) return renderPreview(stegoFile, mediaKind);
  const comparison = await postForm(API.COMPARE, buildFormData({ original: originalFile, stego: stegoFile }));
  return renderComparison({ originalFile, stegoBlob: stegoFile, comparison, title: "Compared with original" });
}

// --- Cards -------------------------------------------------------------------

function verdictBanner(report) {
  const style = VERDICT_STYLES[report.verdict];
  return createElement("div", { className: `verdict verdict--${style.modifier}`, role: "status" }, [
    createElement("div", { className: "verdict__icon", text: style.icon, "aria-hidden": "true" }),
    createElement("div", {}, [
      createElement("div", { className: "verdict__label", text: "Verdict" }),
      createElement("div", { className: "verdict__title", text: report.verdict }),
      createElement("p", { className: "verdict__summary", text: report.summary }),
    ]),
  ]);
}

function checklistCard(report) {
  const items = report.checks.map((check, index) =>
    createElement("li", { className: `checklist__item checklist__item--${check.status}` }, [
      createElement("span", { className: "checklist__icon", text: CHECK_ICONS[check.status], "aria-hidden": "true" }),
      createElement("div", {}, [
        createElement("div", { className: "checklist__name", text: `${index + 1}. ${check.name}` }, [
          createElement("span", { className: "checklist__status", text: check.status }),
        ]),
        createElement("div", { className: "checklist__detail", text: check.detail }),
      ]),
    ]),
  );
  return card([
    createElement("h3", { className: "card__subtitle", text: "Verification checks" }),
    createElement("ol", { className: "checklist" }, items),
    createElement("h3", { className: "section-label", text: "Extraction details" }),
    keyValueList([
      ["Media", orNotApplicable(report.media_description)],
      ["Total slots (N)", formatOptionalNumber(report.slot_count)],
      ["Derived start slot", formatOptionalNumber(report.start_slot)],
      ["LSBs (k) from header", orNotApplicable(report.lsb_count)],
      ["Body length", formatOptionalNumber(report.body_length, " B")],
    ]),
  ]);
}

function hashCard(report) {
  const matches = report.expected_hash_hex === report.computed_hash_hex;
  return card([
    createElement("h3", { className: "card__subtitle", text: matches ? "Media hash matches" : "Media hash mismatch" }),
    createElement("div", { className: "hash-compare" }, [
      hashRow("Signed hash (from payload)", report.expected_hash_hex, report.computed_hash_hex),
      hashRow("Recomputed hash (current file)", report.computed_hash_hex, report.expected_hash_hex),
    ]),
  ]);
}

function hashRow(label, hex, otherHex) {
  const characters = [...hex].map((character, index) =>
    character === otherHex[index] ? document.createTextNode(character) : createElement("span", { className: "hash-diff", text: character }),
  );
  return createElement("div", { className: "hash-compare__row" }, [
    createElement("span", { className: "hash-compare__label", text: label }),
    createElement("span", { className: "mono" }, characters),
  ]);
}
