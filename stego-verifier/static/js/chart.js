// Minimal canvas line/band chart with a legend, crosshair and tooltip.
//
// Each series: { label, colorVar, min: number[], max: number[] }.
// When min === max the series is drawn as a 2px line, otherwise as a band.
// Optional flags: outlineOnly (band edges without fill), dashed (dashed strokes)
// so an overlaid series never hides the one beneath it.

import { createElement } from "./dom.js";
import { formatNumber } from "./format.js";

const LINE_WIDTH = 2;
const BAND_ALPHA = 0.28;
const PADDING = { top: 12, right: 12, bottom: 12, left: 12 };
const GRID_LINE_COUNT = 4;
const CROSSHAIR_WIDTH = 1;
const TOOLTIP_OFFSET_PX = 12;
const DASH_PATTERN = [6, 4];

export function createChart({ series, xLabel, small = false }) {
  const canvas = createElement("canvas", { role: "img", "aria-label": series.map((s) => s.label).join(" vs ") });
  const tooltip = createElement("div", { className: "chart__tooltip", hidden: "" });
  const chart = createElement("div", { className: small ? "chart chart--small" : "chart" }, [canvas, tooltip]);
  const wrapper = createElement("div", {}, [createLegend(series), chart]);
  const state = { canvas, tooltip, series, xLabel, hoverIndex: null };

  new ResizeObserver(() => draw(state)).observe(canvas);
  canvas.addEventListener("pointermove", (event) => handleHover(state, event));
  canvas.addEventListener("pointerleave", () => clearHover(state));
  return wrapper;
}

function createLegend(series) {
  if (series.length < 2) return createElement("div");
  const items = series.map((entry) =>
    createElement("span", { className: "legend__item" }, [
      createElement("span", { className: "legend__swatch", style: `background: var(${entry.colorVar})` }),
      entry.label,
    ]),
  );
  return createElement("div", { className: "legend" }, items);
}

// --- Drawing -----------------------------------------------------------------

function draw(state) {
  const context = prepareCanvas(state.canvas);
  if (!context) return;
  const geometry = computeGeometry(state);
  drawGrid(context, geometry);
  state.series.forEach((entry) => drawSeries(context, geometry, entry));
  if (state.hoverIndex !== null) drawCrosshair(context, geometry, state.hoverIndex);
}

function prepareCanvas(canvas) {
  const { width, height } = canvas.getBoundingClientRect();
  if (width === 0 || height === 0) return null;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const context = canvas.getContext("2d");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  return context;
}

function computeGeometry(state) {
  const { width, height } = state.canvas.getBoundingClientRect();
  const allValues = state.series.flatMap((entry) => [...entry.min, ...entry.max]);
  const low = Math.min(...allValues);
  const high = Math.max(...allValues);
  const span = high - low || 1;
  const pointCount = Math.max(...state.series.map((entry) => entry.max.length));
  const plotWidth = width - PADDING.left - PADDING.right;
  const plotHeight = height - PADDING.top - PADDING.bottom;
  return {
    width,
    height,
    pointCount,
    x: (index) => PADDING.left + (pointCount > 1 ? (index / (pointCount - 1)) * plotWidth : plotWidth / 2),
    y: (value) => PADDING.top + (1 - (value - low) / span) * plotHeight,
    indexAt: (pixelX) => clamp(Math.round(((pixelX - PADDING.left) / plotWidth) * (pointCount - 1)), 0, pointCount - 1),
  };
}

function drawGrid(context, geometry) {
  context.strokeStyle = cssVar("--chart-grid");
  context.lineWidth = 1;
  for (let line = 0; line <= GRID_LINE_COUNT; line += 1) {
    const y = PADDING.top + (line / GRID_LINE_COUNT) * (geometry.height - PADDING.top - PADDING.bottom);
    context.beginPath();
    context.moveTo(PADDING.left, y);
    context.lineTo(geometry.width - PADDING.right, y);
    context.stroke();
  }
}

function drawSeries(context, geometry, entry) {
  const color = cssVar(entry.colorVar);
  const band = isBand(entry);
  const dashed = entry.dashed || entry.outlineOnly;
  if (band && !entry.outlineOnly) drawBand(context, geometry, entry, color);
  drawPolyline(context, geometry, entry.max, color, dashed);
  if (band) drawPolyline(context, geometry, entry.min, color, dashed);
}

function drawBand(context, geometry, entry, color) {
  context.beginPath();
  entry.max.forEach((value, index) => context.lineTo(geometry.x(index), geometry.y(value)));
  for (let index = entry.min.length - 1; index >= 0; index -= 1) {
    context.lineTo(geometry.x(index), geometry.y(entry.min[index]));
  }
  context.closePath();
  context.globalAlpha = BAND_ALPHA;
  context.fillStyle = color;
  context.fill();
  context.globalAlpha = 1;
}

function drawPolyline(context, geometry, values, color, dashed) {
  context.setLineDash(dashed ? DASH_PATTERN : []);
  context.beginPath();
  values.forEach((value, index) => context.lineTo(geometry.x(index), geometry.y(value)));
  context.strokeStyle = color;
  context.lineWidth = LINE_WIDTH;
  context.lineJoin = "round";
  context.stroke();
  context.setLineDash([]);
}

function drawCrosshair(context, geometry, index) {
  context.strokeStyle = cssVar("--color-text-muted");
  context.lineWidth = CROSSHAIR_WIDTH;
  context.beginPath();
  context.moveTo(geometry.x(index), PADDING.top);
  context.lineTo(geometry.x(index), geometry.height - PADDING.bottom);
  context.stroke();
}

// --- Hover -------------------------------------------------------------------

function handleHover(state, event) {
  const bounds = state.canvas.getBoundingClientRect();
  const geometry = computeGeometry(state);
  state.hoverIndex = geometry.indexAt(event.clientX - bounds.left);
  draw(state);
  showTooltip(state, geometry);
}

function clearHover(state) {
  state.hoverIndex = null;
  state.tooltip.hidden = true;
  draw(state);
}

function showTooltip(state, geometry) {
  const index = state.hoverIndex;
  const lines = [state.xLabel(index), ...state.series.map((entry) => `${entry.label}: ${describePoint(entry, index)}`)];
  state.tooltip.replaceChildren(...lines.map((line) => createElement("div", { text: line })));
  state.tooltip.style.left = `${geometry.x(index)}px`;
  state.tooltip.style.top = `${TOOLTIP_OFFSET_PX + PADDING.top}px`;
  state.tooltip.hidden = false;
}

function describePoint(entry, index) {
  const low = entry.min[index];
  const high = entry.max[index];
  return low === high ? formatNumber(high) : `${formatNumber(low)} … ${formatNumber(high)}`;
}

// --- Utilities ---------------------------------------------------------------

function isBand(entry) {
  return entry.min.some((value, index) => value !== entry.max[index]);
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function clamp(value, low, high) {
  return Math.min(high, Math.max(low, value));
}
