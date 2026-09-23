// Before/after comparison card shared by the Protect and Verify tabs.

import { MEDIA_KIND, PNG_MIME_TYPE } from "./constants.js";
import { card, createElement, sectionLabel, statGrid } from "./dom.js";
import { createChart } from "./chart.js";
import { base64ToBlob, formatDecibels, formatPreciseMetric, formatNumber, formatPercent } from "./format.js";

const ORIGINAL_LABEL = "Cover (original)";
const STEGO_LABEL = "Stego";

/** Build the comparison card for an original file and its stego version. */
export function renderComparison({ originalFile, stegoBlob, comparison, title = "Before and after" }) {
  const body = comparison.media_kind === MEDIA_KIND.IMAGE
    ? imageComparison(originalFile, stegoBlob, comparison)
    : audioComparison(originalFile, stegoBlob, comparison);
  return card([createElement("h3", { className: "card__subtitle", text: title }), ...body]);
}

/** Preview a single file (no original to compare against). */
export function renderPreview(file, mediaKind, title = "Stego file") {
  const media = mediaKind === MEDIA_KIND.IMAGE ? imageElement(file, title) : audioElement(file);
  return card([createElement("h3", { className: "card__subtitle", text: title }), media]);
}

// --- Image -------------------------------------------------------------------

function imageComparison(originalFile, stegoBlob, comparison) {
  return [
    mediaPair(imageElement(originalFile, ORIGINAL_LABEL), imageElement(stegoBlob, STEGO_LABEL)),
    statGrid([
      ["PSNR", formatDecibels(comparison.psnr_db)],
      ["MSE", formatPreciseMetric(comparison.mse)],
      ["Values changed", formatPercent(comparison.changed_values, comparison.total_values)],
      ["Max change", formatNumber(comparison.max_difference)],
    ]),
    sectionLabel("Amplified difference map"),
    createElement("p", { className: "section-hint", text: "Brighter pixels changed more. The payload is the band starting at the secret start slot." }),
    imageElement(base64ToBlob(comparison.difference_map_png, PNG_MIME_TYPE), "Difference map"),
  ];
}

// --- Audio -------------------------------------------------------------------

function audioComparison(originalFile, stegoBlob, comparison) {
  const bucketCount = comparison.waveform.original.max.length;
  const timeLabel = (index) => `≈ ${((index / Math.max(bucketCount - 1, 1)) * comparison.duration_seconds).toFixed(2)} s`;
  return [
    mediaPair(audioElement(originalFile), audioElement(stegoBlob)),
    statGrid([
      ["SNR", formatDecibels(comparison.snr_db)],
      ["Samples changed", formatPercent(comparison.changed_samples, comparison.total_samples)],
      ["Max change", formatNumber(comparison.max_difference)],
    ]),
    sectionLabel("Waveform (channel 1)"),
    createChart({
      series: [
        envelopeSeries(ORIGINAL_LABEL, "--chart-series-1", comparison.waveform.original),
        { ...envelopeSeries(STEGO_LABEL, "--chart-series-2", comparison.waveform.stego), outlineOnly: true },
      ],
      xLabel: timeLabel,
    }),
    sectionLabel("Difference (stego − original, auto-scaled)"),
    createChart({
      series: [envelopeSeries("Difference", "--chart-series-2", comparison.waveform.difference)],
      xLabel: timeLabel,
      small: true,
    }),
    ...zoomChart(comparison.zoom),
  ];
}

function zoomChart(zoom) {
  return [
    sectionLabel(`Zoom: samples ${formatNumber(zoom.start_sample)}–${formatNumber(zoom.start_sample + zoom.original.length)}`),
    createElement("p", { className: "section-hint", text: "Sample-level view around the first modified sample (the payload start)." }),
    createChart({
      series: [
        lineSeries(ORIGINAL_LABEL, "--chart-series-1", zoom.original),
        { ...lineSeries(STEGO_LABEL, "--chart-series-2", zoom.stego), dashed: true },
      ],
      xLabel: (index) => `Sample ${formatNumber(zoom.start_sample + index)}`,
    }),
  ];
}

function envelopeSeries(label, colorVar, envelope) {
  return { label, colorVar, min: envelope.min, max: envelope.max };
}

function lineSeries(label, colorVar, values) {
  return { label, colorVar, min: values, max: values };
}

// --- Shared elements -----------------------------------------------------------

function mediaPair(originalElement, stegoElement) {
  return createElement("div", { className: "media-pair" }, [
    labelledItem(ORIGINAL_LABEL, originalElement),
    labelledItem(STEGO_LABEL, stegoElement),
  ]);
}

function labelledItem(label, element) {
  return createElement("div", { className: "media-pair__item" }, [
    createElement("span", { className: "media-pair__label", text: label }),
    element,
  ]);
}

function imageElement(blob, altText) {
  return createElement("img", { className: "media-pair__image", src: URL.createObjectURL(blob), alt: altText });
}

function audioElement(blob) {
  return createElement("audio", { controls: "", preload: "metadata", src: URL.createObjectURL(blob) });
}
