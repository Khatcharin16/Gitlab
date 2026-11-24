// Lab 04 UI state only.  All numbers and SVG points still come from ngspice.
(function () {
  "use strict";

  var form = document.getElementById("spice-main-form");
  if (!form) return;

  var status = document.getElementById("running-status");
  var mode = document.getElementById("running-mode");
  var buttons = Array.prototype.slice.call(
    document.querySelectorAll('button[type="submit"][form="spice-main-form"], ' +
      '#spice-main-form button[type="submit"]')
  );
  var regions = Array.prototype.slice.call(
    document.querySelectorAll(".block-results, .block-plots")
  );
  var original = [];

  function labels() {
    return { dc: "DC .op", ac: "AC .ac", tran: "Transient .tran" };
  }

  function restore() {
    buttons.forEach(function (button, index) {
      if (original[index] !== undefined) button.innerHTML = original[index];
      button.disabled = false;
      button.removeAttribute("aria-busy");
    });
    regions.forEach(function (region) {
      region.removeAttribute("aria-busy");
    });
    if (status) status.hidden = true;
  }

  form.addEventListener("submit", function () {
    original = buttons.map(function (button) { return button.innerHTML; });
    // The mode radios live in Block 2 and are associated through form="".
    var selected = document.querySelector('input[name="analysis"]:checked');
    var key = selected ? selected.value : "dc";
    if (mode) mode.textContent = labels()[key] || key;
    if (status) status.hidden = false;
    buttons.forEach(function (button) {
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.textContent = "Running…";
    });
    regions.forEach(function (region) {
      region.setAttribute("aria-busy", "true");
    });
  });

  window.addEventListener("pageshow", restore);
}());
