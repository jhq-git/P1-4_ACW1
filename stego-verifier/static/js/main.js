// Entry point: load protocol limits, then initialise every tab.

import { API } from "./constants.js";
import { initTabs } from "./tabs.js";
import { initDropzones, initSecretToggles } from "./form-controls.js";
import { initKeysTab } from "./keys-tab.js";
import { initProtectTab } from "./protect-tab.js";
import { initVerifyTab } from "./verify-tab.js";

async function loadLimits() {
  const response = await fetch(API.LIMITS);
  return response.json();
}

async function main() {
  initTabs();
  initDropzones();
  initSecretToggles();
  initKeysTab();
  initVerifyTab();
  initProtectTab(await loadLimits());
}

main();
