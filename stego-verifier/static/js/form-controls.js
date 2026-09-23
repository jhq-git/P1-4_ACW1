// Reusable behaviour for dropzones, secret inputs and byte counters.

import { utf8ByteLength } from "./format.js";

const DRAGGING_CLASS = "is-dragging";
const HAS_FILE_CLASS = "has-file";
const ERROR_CLASS = "is-error";
const SHOW_LABEL = "Show";
const HIDE_LABEL = "Hide";
const REVEALED_CLASS = "is-revealed";

/** Wire every [data-dropzone] label: drag-and-drop plus a filename title. */
export function initDropzones() {
  document.querySelectorAll("[data-dropzone]").forEach(initDropzone);
}

/** Wire every [data-toggle-secret] button to show/hide its masked input. */
export function initSecretToggles() {
  document.querySelectorAll("[data-toggle-secret]").forEach((button) => {
    const input = document.getElementById(button.dataset.toggleSecret);
    button.addEventListener("click", () => toggleSecret(input, button));
  });
}

/** Show "used / max bytes" under a text input and flag overflow. */
export function bindByteCounter(input, counter, maxBytes) {
  const update = () => {
    const used = utf8ByteLength(input.value);
    counter.textContent = `${used} / ${maxBytes} bytes`;
    counter.classList.toggle(ERROR_CLASS, used > maxBytes);
  };
  input.addEventListener("input", update);
  update();
}

export function setMeta(element, text, isError = false) {
  element.textContent = text;
  element.classList.toggle(ERROR_CLASS, isError);
}

function initDropzone(zone) {
  const input = zone.querySelector('input[type="file"]');
  const title = zone.querySelector("[data-dropzone-title]");
  const defaultTitle = title.textContent;
  input.addEventListener("change", () => updateTitle(zone, title, input, defaultTitle));
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add(DRAGGING_CLASS);
  });
  zone.addEventListener("dragleave", () => zone.classList.remove(DRAGGING_CLASS));
  zone.addEventListener("drop", (event) => dropFile(event, zone, input));
}

function dropFile(event, zone, input) {
  event.preventDefault();
  zone.classList.remove(DRAGGING_CLASS);
  if (event.dataTransfer.files.length === 0) return;
  input.files = event.dataTransfer.files;
  input.dispatchEvent(new Event("change"));
}

function updateTitle(zone, title, input, defaultTitle) {
  const file = input.files[0];
  title.textContent = file ? file.name : defaultTitle;
  zone.classList.toggle(HAS_FILE_CLASS, Boolean(file));
}

function toggleSecret(input, button) {
  const isRevealed = input.classList.toggle(REVEALED_CLASS);
  button.textContent = isRevealed ? HIDE_LABEL : SHOW_LABEL;
}
