// Formatting and file helpers.

import { PERCENT } from "./constants.js";

const textEncoder = new TextEncoder();
const numberFormat = new Intl.NumberFormat();
const PERCENT_DECIMALS = 1;
const METRIC_DECIMALS = 2;
const PRECISE_METRIC_DECIMALS = 5;
const NOT_APPLICABLE = "—";
const INFINITE_LABEL = "∞ (identical)";
const OBJECT_URL_REVOKE_DELAY_MS = 1000;

export function formatNumber(value) {
  return numberFormat.format(value);
}

export function formatPercent(part, whole) {
  return `${((part / whole) * PERCENT).toFixed(PERCENT_DECIMALS)}%`;
}

export function formatDecibels(value) {
  return value === null ? INFINITE_LABEL : `${value.toFixed(METRIC_DECIMALS)} dB`;
}

export function formatPreciseMetric(value) {
  return value === null || value === undefined ? NOT_APPLICABLE : value.toFixed(PRECISE_METRIC_DECIMALS);
}

export function formatTimestamp(isoString) {
  return new Date(isoString).toLocaleString();
}

export function utf8ByteLength(text) {
  return textEncoder.encode(text).length;
}

export function base64ToBlob(base64, mimeType) {
  const binary = atob(base64);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return new Blob([bytes], { type: mimeType });
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), OBJECT_URL_REVOKE_DELAY_MS);
}

export function orNotApplicable(value) {
  return value === null || value === undefined ? NOT_APPLICABLE : String(value);
}

export function formatOptionalNumber(value, suffix = "") {
  return value === null || value === undefined ? NOT_APPLICABLE : `${formatNumber(value)}${suffix}`;
}
