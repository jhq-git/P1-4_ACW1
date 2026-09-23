// Small DOM helpers used by every view.

export function byId(id) {
  return document.getElementById(id);
}

/**
 * Create an element. `attributes` may include `className`, `text`, `dataset`
 * and any regular attribute; `children` are nodes or strings.
 */
export function createElement(tag, attributes = {}, children = []) {
  const element = document.createElement(tag);
  const { className, text, dataset, ...rest } = attributes;
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  if (dataset) Object.assign(element.dataset, dataset);
  Object.entries(rest).forEach(([name, value]) => element.setAttribute(name, value));
  children.forEach((child) => element.append(child));
  return element;
}

export function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

export function hideError(element) {
  element.textContent = "";
  element.hidden = true;
}

export async function withBusyButton(button, busyLabel, task) {
  const idleLabel = button.textContent;
  button.disabled = true;
  button.textContent = busyLabel;
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.textContent = idleLabel;
  }
}

export function replaceChildren(container, children) {
  container.replaceChildren(...children);
}

export function card(children, className = "") {
  return createElement("div", { className: `card ${className}`.trim() }, children);
}

export function sectionLabel(text) {
  return createElement("h3", { className: "section-label", text });
}

export function keyValueList(rows) {
  const list = createElement("div", { className: "kv" });
  rows.forEach(([key, value]) => {
    list.append(createElement("div", { className: "kv__key", text: key }));
    list.append(value instanceof Node ? wrapValue(value) : createElement("div", { className: "kv__value", text: value }));
  });
  return list;
}

export function statGrid(stats) {
  return createElement(
    "div",
    { className: "stats" },
    stats.map(([label, value]) =>
      createElement("div", { className: "stat" }, [
        createElement("div", { className: "stat__label", text: label }),
        createElement("div", { className: "stat__value", text: value }),
      ]),
    ),
  );
}

function wrapValue(node) {
  return createElement("div", { className: "kv__value" }, [node]);
}
