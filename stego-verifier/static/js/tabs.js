// Accessible tab switching.

const ACTIVE_CLASS = "is-active";

export function initTabs() {
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  tabs.forEach((tab) => tab.addEventListener("click", () => activateTab(tabs, tab)));
}

function activateTab(tabs, selectedTab) {
  tabs.forEach((tab) => {
    const isSelected = tab === selectedTab;
    const panel = document.getElementById(tab.getAttribute("aria-controls"));
    tab.classList.toggle(ACTIVE_CLASS, isSelected);
    tab.setAttribute("aria-selected", String(isSelected));
    panel.classList.toggle(ACTIVE_CLASS, isSelected);
    panel.hidden = !isSelected;
  });
}
