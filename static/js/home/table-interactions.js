// Callbacks related to interacting with table rows
require(["jquery", "home/utils"], function (
  $,
  utils,
) {
  "use strict";

  // Toggle a labs corresponding collapsible table row 
  // when it's summary table row is clicked.
  $(".summary-tr").on("click", function () {
    let id = $(this).data("server-id");
    let accordionIcon = $(this).find(".accordion-icon");
    let collapse = $(`.collapse[id*=${id}]`);
    let shown = collapse.hasClass("show");
    if (shown) accordionIcon.addClass("collapsed");
    else accordionIcon.removeClass("collapsed");
    new bootstrap.Collapse(collapse);
  });

  // ... but not when the action td button are clicked.
  $(".actions-td button").on("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
  });

  // We show warning icons when the content of tabs change.
  // Hide those warning icons once the tab is activated.
  $("button[role=tab]").on("click", function () {
    let warning = $(this).find("[id$=tab-warning]");
    warning.addClass("invisible");
  });

  // Toggle log tabs on log button or log info text click
  $(".log-info-btn, .log-info-text").on("click", function (event) {
    let id = $(this).parents("tr").data("server-id");
    let collapse = $(`.collapse[id*=${id}]`);
    let shown = collapse.hasClass("show");
    // Prevent collapse from closing if it is  
    // already open, but not showing the logs tab.
    if (shown && !$(`#${id}-logs-tab`).hasClass("active")) {
      event.preventDefault();
      event.stopPropagation();
    }
    // Change to the log tab.
    var trigger = $(`#${id}-logs-tab`);
    var tab = new bootstrap.Tab(trigger);
    tab.show();
  });

  // Show selected logs.
  $("select[id*=log-select]").change(function () {
    const id = utils.getId(this);
    const val = $(this).val();
    var log = $(`#${id}-log`);
    log.html("");
    for (const event of spawnEvents[id][val]) {
      utils.appendToLog(log, event["html_message"]);
    }
  });

})