// Callbacks related to interacting with table rows
require(["jquery", "home/utils", "home/dropdown-options"], function (
  $,
  utils,
  dropdowns
) {
  "use strict";

  /* *************** */
  /* TABLE UI EVENTS */
  /* *************** */

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


  /* *************** */
  /* LAB CONFIG      */
  /* *************** */

  function _toggle_show_input(id, key, pattern) {
    const showInput = $(`input#${id}-${key}-cb-input`)[0].checked;
    if (showInput) {
      $(`#${id}-${key}-input-div`).show();
      $(`#${id}-${key}-input`).attr("required", true);
      if (pattern) $(`#${id}-${key}-input`).attr("pattern", pattern);
    } else {
      $(`#${id}-${key}-input-div`).hide();
      $(`#${id}-${key}-input`).removeAttr("required pattern");
    }
  }

  $("select[id*=version]").change(function () {
    const id = utils.getId(this);
    const values = utils.getLabConfigSelectValues(id);
    if (!$(this).hasClass("no-update")) {
      try {
        dropdowns.updateSystems(id, values.service);
      }
      catch (e) {
        utils.setLabAsNA(id, "due to a JS error");
        console.log(e);
      }
    }

    const serviceInfo = getServiceInfo();
    const userInputInfo = (serviceInfo.JupyterLab.options[values.service] || {}).userInput || {};
    var customImageInput = $(`input#${id}-image-input`);
    var customMountInput = $(`#${id}-image-mount-input`);
    var allUserInputDivs = $(`#${id}-image-input-div, #${id}-image-mount-cb-input-div, #${id}-image-mount-input-div`)

    var inputRequired = userInputInfo.required || false;
    if (!inputRequired) {
      dropdowns.resetInputElement(customImageInput, false);
      dropdowns.resetInputElement(customMountInput, false);
      allUserInputDivs.hide();
    } else {
      dropdowns.resetInputElement(customImageInput, true);
      allUserInputDivs.show();
      // Enable user data mount by default
      $(`#${id}-image-mount-cb-input`)[0].checked = userInputInfo.defaultMountEnabled || true;;
      customMountInput.val(userInputInfo.defaultMountPath || "/mnt/userdata");
    }
  });

  $("input[id*=image-mount-cb-input]").change(function () {
    const id = utils.getId(this, -4);
    const pattern_check = "^\\/[A-Za-z0-9\\-\\/]+";
    _toggle_show_input(id, "image-mount", pattern_check);
  });

  $("select[id*=system]").change(function () {
    const id = utils.getId(this);
    const values = utils.getLabConfigSelectValues(id);
    if (!$(this).hasClass("no-update")) {
      try {
        dropdowns.updateFlavors(id, values.service, values.system);
        dropdowns.updateAccounts(id, values.service, values.system);
      }
      catch (e) {
        utils.setLabAsNA(id, "due to a JS error");
        console.log(e);
      }
    }

    // Check if the chosen version is deprecated for the system
    const serviceInfo = getServiceInfo();
    const systemInfo = getSystemInfo();
    // First check for system specific default option, then for general one
    var defaultOption = (((systemInfo[values.system] || {}).services || {}).JupyterLab || {}).defaultOption || serviceInfo.JupyterLab.defaultOption;
    if (defaultOption && values.service != defaultOption) {
      // Not using default/latest version, show a warning message
      let reason = "<span style=\"color:darkorange;\">uses deprecated version</span>";
      $(`#${id}-spawner-info`).show().html(reason);
    }
    else {
      $(`#${id}-spawner-info`).hide().html("");
    }
  });

  $("select[id*=account]").change(function () {
    const id = utils.getId(this);
    const values = utils.getLabConfigSelectValues(id);
    if (!$(this).hasClass("no-update")) {
      try {
        dropdowns.updateProjects(id, values.service, values.system, values.account);
      }
      catch (e) {
        utils.setLabAsNA(id, "due to a JS error");
        console.log(e);
      }
    }
  });

  $("select[id*=project]").change(function () {
    const id = utils.getId(this);
    const values = utils.getLabConfigSelectValues(id);
    if (!$(this).hasClass("no-update")) {
      try {
        dropdowns.updatePartitions(id, values.service, values.system, values.account, values.project);
      }
      catch (e) {
        utils.setLabAsNA(id, "due to a JS error");
        console.log(e);
      }
    }
  });

  $("select[id*=partition]").change(function () {
    const id = utils.getId(this);
    const values = utils.getLabConfigSelectValues(id);
    if (!$(this).hasClass("no-update")) {
      try {
        dropdowns.updateReservations(id, values.service, values.system, values.account, values.project, values.partition);
        dropdowns.updateResources(id, values.service, values.system, values.account, values.project, values.partition);
        dropdowns.updateModules(id, values.service, values.system, values.account, values.project, values.partition);
      }
      catch (e) {
        utils.setLabAsNA(id, "due to a JS error");
        console.log(e);
      }
    }
  });

  $("input[id*=xserver-cb-input]").change(function () {
    const id = utils.getId(this, -3);
    _toggle_show_input(id, "xserver");
  });

  $("select[id*=reservation]").change(function () {
    const reservationInfo = getReservationInfo();

    const id = utils.getId(this);
    const value = $(this).val();
    if (value) {
      if (value == "None") {
        $(`#${id}-reservation-info-div`).hide();
        return;
      }
      const systemReservationInfo = reservationInfo[utils.getLabConfigSelectValues(id)["system"]] || [];
      for (const reservationInfo of systemReservationInfo) {
        if (reservationInfo.ReservationName == value) {
          $(`#${id}-reservation-start`).html(reservationInfo.StartTime);
          $(`#${id}-reservation-end`).html(reservationInfo.EndTime);
          $(`#${id}-reservation-state`).html(reservationInfo.State);
          $(`#${id}-reservation-details`).html(
            JSON.stringify(reservationInfo, null, 2));
        }
      }
      $(`#${id}-reservation-info-div`).show();
    }
    else {
      $(`#${id}-reservation-info-div`).hide();
    }
  });

  $("input.module-selector").click(function () {
    const id = utils.getId(this, slice_index = 1);
    const allOrNone = $(this).attr("id").includes("select-all") ? "all" : "none";
    var checkboxes = $(`#${id}-modules-form`).find("input[type=checkbox]");
    if (allOrNone == "all") {
      $(`#${id}-modules-select-none`)[0].checked = false;
      checkboxes.each((i, cb) => { cb.checked = true; });
    }
    else if (allOrNone == "none") {
      $(`#${id}-modules-select-all`)[0].checked = false;
      checkboxes.each((i, cb) => { cb.checked = false; });
    }
  });

})