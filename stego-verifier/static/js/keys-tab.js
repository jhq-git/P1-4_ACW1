// Keys tab: generate an Ed25519 key pair and offer both halves for download.

import { API, KEY_FILENAMES, PEM_MIME_TYPE } from "./constants.js";
import { postForm } from "./api.js";
import { byId, hideError, showError, withBusyButton } from "./dom.js";
import { downloadBlob } from "./format.js";

export function initKeysTab() {
  const elements = {
    generate: byId("keys-generate"),
    downloads: byId("keys-downloads"),
    downloadPrivate: byId("keys-download-private"),
    downloadPublic: byId("keys-download-public"),
    error: byId("keys-error"),
  };
  const state = { keyPair: null };

  elements.generate.addEventListener("click", () => generateKeys(elements, state));
  elements.downloadPrivate.addEventListener("click", () => downloadPem(state.keyPair.private_pem, KEY_FILENAMES.PRIVATE));
  elements.downloadPublic.addEventListener("click", () => downloadPem(state.keyPair.public_pem, KEY_FILENAMES.PUBLIC));
}

async function generateKeys(elements, state) {
  hideError(elements.error);
  try {
    state.keyPair = await withBusyButton(elements.generate, "Generating…", () => postForm(API.KEYS, new FormData()));
    elements.downloads.hidden = false;
    elements.generate.textContent = "Generate a new key pair";
  } catch (error) {
    showError(elements.error, error.message);
  }
}

function downloadPem(pem, filename) {
  downloadBlob(new Blob([pem], { type: PEM_MIME_TYPE }), filename);
}
