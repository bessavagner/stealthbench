/*
 * sannysoft.checks.js — a self-hosted, offline, Sannysoft-style automation-detection panel.
 *
 * This reproduces the NAVIGATOR-PROPERTY / automation-flag surface that bot.sannysoft.com
 * renders (webdriver flag, plugins/mimeTypes, languages, window.chrome, permissions mismatch,
 * PhantomJS / Selenium / chromedriver markers, WebGL vendor/renderer, outer dimensions,
 * native-function integrity). It is a CREDITED REPRODUCTION of well-known open checks — it
 * runs entirely from navigator/window reads with ZERO network access, no blocking dialogs,
 * and no required user interaction, so it can be measured unattended and served fully offline.
 *
 * Attribution (all MIT — see ./LICENSE):
 *   - antoinevastel/fpscanner + fpcollect  (WEBDRIVER / HEADCHR_* / PHANTOM_* / SELENIUM checks)
 *   - intoli/intoli-article-materials       (user-agent / plugins / languages / webgl checks)
 *   - infosimples/detect-headless           (plugins/mime prototype + permissions + outer checks)
 *
 * DOM CONTRACT (consumed by detectors/sannysoft.py):
 *   - Each check renders one <tr class="check passed"> or <tr class="check failed"> into <table id="results">.
 *     `passed`  = the browser looks human/headful for that check.
 *     `failed`  = an automation/headless signal was detected.
 *     A check that throws renders <tr class="check errored"> and is EXCLUDED from the counts
 *     (a gap, never a fabricated pass or fail).
 *   - When every check has resolved, window.__SANNYSOFT_DONE__ is set to true.
 *   - The detector waits on __SANNYSOFT_DONE__, then reduces rows to integer counts
 *     {passed, failed, total} IN-BROWSER — no row text ever returns to Python.
 */
(function () {
  "use strict";

  // Each check returns true (human/headful, pass) or false (automation detected, fail).
  // Throwing is allowed — the check is then recorded as "errored" and excluded from counts.
  const CHECKS = [
    ["webdriver", () => navigator.webdriver === false],
    ["user-agent", () => !/headless/i.test(navigator.userAgent)],
    ["app-version", () => !/headless/i.test(navigator.appVersion || "")],
    ["plugins-length", () => navigator.plugins.length > 0],
    ["plugins-prototype", () => {
      let ok = PluginArray.prototype === Object.getPrototypeOf(navigator.plugins);
      if (navigator.plugins.length > 0) {
        ok = ok && Plugin.prototype === Object.getPrototypeOf(navigator.plugins[0]);
      }
      return ok;
    }],
    ["mime-types", () => navigator.mimeTypes.length > 0],
    ["languages", () =>
      Array.isArray(navigator.languages) && navigator.languages.length > 0 && !!navigator.language],
    ["language-consistency", () => navigator.language === navigator.languages[0]],
    ["chrome-object", () => typeof window.chrome !== "undefined" && window.chrome !== null],
    ["permissions-mismatch", async () => {
      if (!navigator.permissions || typeof Notification === "undefined") return true;
      const status = await navigator.permissions.query({ name: "notifications" });
      // The classic headless tell: Notification denied while the permission query says "prompt".
      return !(Notification.permission === "denied" && status.state === "prompt");
    }],
    ["phantom-properties", () =>
      !(window._phantom || window.__phantomas || window.callPhantom)],
    ["selenium-properties", () => {
      const w = window, d = document;
      return !(
        w._selenium || w._Selenium_IDE_Recorder || w.__webdriver_evaluate ||
        w.__selenium_evaluate || w.__webdriver_script_function || w.__webdriver_script_func ||
        w.__webdriver_script_fn || w.__fxdriver_evaluate || w.__driver_evaluate ||
        d.__selenium_unwrapped || d.__webdriver_evaluate || d.__driver_evaluate ||
        d.selenium || d.__webdriver_script_fn
      );
    }],
    ["chromedriver-cdc", () => {
      const hit = (obj) => {
        try { return Object.keys(obj).some((k) => /^[$]?cdc_|_selenium|webdriver/i.test(k)); }
        catch (e) { return false; }
      };
      return !(hit(window) || hit(document));
    }],
    ["webgl-renderer", () => {
      const gl = document.createElement("canvas").getContext("webgl") ||
                 document.createElement("canvas").getContext("experimental-webgl");
      if (!gl) throw new Error("no webgl");
      const ext = gl.getExtension("WEBGL_debug_renderer_info");
      const renderer = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : "";
      return !/swiftshader|mesa offscreen|llvmpipe/i.test(renderer);
    }],
    ["outer-dimensions", () => window.outerWidth > 0 && window.outerHeight > 0],
    ["hardware-concurrency", () => navigator.hardwareConcurrency > 0],
    ["native-permissions-query", () => {
      if (!navigator.permissions) return true; // absent API is not a stealth patch
      return Function.prototype.toString.call(navigator.permissions.query).includes("[native code]");
    }],
    ["iframe-chrome", async () => {
      const iframe = document.createElement("iframe");
      iframe.style.display = "none";
      iframe.srcdoc = "<!doctype html>";
      document.body.appendChild(iframe);
      try {
        await new Promise((res) => { iframe.onload = res; setTimeout(res, 500); });
        // A stealth patch that only touches the top window leaks a bare iframe context.
        return typeof iframe.contentWindow.chrome !== "undefined" ||
               typeof window.chrome === "undefined"; // Firefox has neither: not a Chrome-stealth leak
      } finally {
        iframe.remove();
      }
    }],
  ];

  const table = document.getElementById("results");

  function addRow(name, verdict) {
    const tr = document.createElement("tr");
    tr.className = "check " + verdict; // passed | failed | errored
    const nameCell = document.createElement("td");
    nameCell.textContent = name;
    const resultCell = document.createElement("td");
    resultCell.textContent = verdict;
    tr.appendChild(nameCell);
    tr.appendChild(resultCell);
    table.appendChild(tr);
  }

  async function run() {
    for (const [name, fn] of CHECKS) {
      let verdict;
      try {
        const ok = await fn();
        verdict = ok ? "passed" : "failed";
      } catch (e) {
        verdict = "errored";
      }
      addRow(name, verdict);
    }
    window.__SANNYSOFT_DONE__ = true;
    document.title = "SANNYSOFT_DONE";
  }

  run();
})();
