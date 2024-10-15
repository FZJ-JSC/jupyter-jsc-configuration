/*
* Callbacks related to interacting with table rows
*/
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

  $("button[id*=view-password]").on("click", function (event) {
    const id = utils.getId(this);
    const passInput = $(`#${id}-image-private-pass-input`)[0]
    const eye = $(`#${id}-password-eye`)[0]
    if (passInput.type === 'password') {
      passInput.type = 'text';
      eye.classList.remove('fa-eye');
      eye.classList.add('fa-eye-slash');
    } else {
      passInput.type = 'password';
      eye.classList.add('fa-eye');
      eye.classList.remove('fa-eye-slash');
    }
  });

  /* *************** */
  /* LAB CONFIG      */
  /* *************** */

  function _toggle_show_element(id, key, type, showInput, pattern) {
    if (showInput) {
      $(`#${id}-${key}-${type}-div`).show();
      $(`#${id}-${key}-${type}`).attr("required", true);
      if (pattern) $(`#${id}-${key}-${type}`).attr("pattern", pattern);
    } else {
      $(`#${id}-${key}-${type}-div`).hide();
      $(`#${id}-${key}-${type}`).removeAttr("required pattern");
    }
  }

  function _toggle_show_repo2Docker(id, show){
    var repo2DockerInputs = ["repo", "gitref", "notebook"];
    var repo2DockerSelects = ["type", "notebook_type"]

    var show = userInputInfo.isRepo2Docker || false;
    for(let key of repo2DockerInputs){
      let element = $(`#${id}-${key}-input`);
      dropdowns.resetInputElement(element, false);
      _toggle_show_element(id, key, "input", show);
    }
    repo2DockerSelects.forEach(key => _toggle_show_element(id, key, "select", show));
  }

  function _toggle_show_customImage(id, values){
    const serviceInfo = getServiceInfo();
    const userInputInfo = (serviceInfo.JupyterLab.options[values.service] || {}).userInput || {};

    var customImageInput = $(`input#${id}-image-input`);
    var customMountInput = $(`#${id}-image-mount-input`);
    var registryAuthsInputs = $(`#${id}-image-private-url-input, #${id}-image-private-user-input, #${id}-image-private-pass-input`);

    var registryAuthsInputDivs = $(`#${id}-image-private-url-input-div,#${id}-image-private-user-input-div, #${id}-image-private-pass-input-div`)
    var allUserInputDivs = $(`#${id}-image-input-div, #${id}-image-private-cb-input-div, #${id}-image-mount-cb-input-div, #${id}-image-mount-input-div`)

    var inputRequired = userInputInfo.required || false;
    if (!inputRequired) {
      dropdowns.resetInputElement(customImageInput, false);
      dropdowns.resetInputElement(customMountInput, false);
      dropdowns.resetInputElement(registryAuthsInputs, false);

      registryAuthsInputDivs.hide();
      allUserInputDivs.hide();
      // TODO fix the share button visibility
      $(`#${id}-share-btn`).hide();
    } else {
      dropdowns.resetInputElement(customImageInput, true);

      // Set default values for the private docker registry authentications to false => fields are hidden and not required
      $(`#${id}-image-private-cb-input`)[0].checked = false;
      dropdowns.resetInputElement(registryAuthsInputs, false);
      allUserInputDivs.show();
      // TODO fix the share button visibility
      $(`#${id}-share-btn`).show();

      // Enable user data mount by default
      $(`#${id}-image-mount-cb-input`)[0].checked = userInputInfo.defaultMountEnabled || true;;
      customMountInput.val(userInputInfo.defaultMountPath || "/mnt/userdata");
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

    _toggle_show_customImage(id, values);
    _toggle_show_repo2Docker(id);
  
  });

  $("input[id*=image-private-cb-input]").change(function () {
    const id = utils.getId(this, -4);
    const showInput = this.checked;
    _toggle_show_element(id, "image-private-url", "input", showInput);
    _toggle_show_element(id, "image-private-user", "input", showInput);
    _toggle_show_element(id, "image-private-pass", "input", showInput);
  });

  $("input[id*=image-mount-cb-input]").change(function () {
    const id = utils.getId(this, -4);
    const pattern_check = "^\\/[A-Za-z0-9\\-\\/]+";
    _toggle_show_element(id, "image-mount", "input", this.checked, pattern_check);
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
    _toggle_show_element(id, "xserver", "input", this.checked);
  });

  $("select[id*=reservation]").change(function () {
    const reservationInfo = getReservationInfo();

    const id = utils.getId(this);
    const value = $(this).val();
    if (value) {
      if (value == "None") {
        $(`#${id}-reservation-info-div`).hide();
        $(`#${id}-runtime-input`).trigger("change");
        // }
        return;
      }
      const systemReservationInfo = reservationInfo[utils.getLabConfigSelectValues(id)["system"]] || [];
      for (const reservationInfo of systemReservationInfo) {
        if (reservationInfo.ReservationName == value) {
          $(`#${id}-reservation-start`).html(`${reservationInfo.StartTime} (Europe/Berlin)`);
          $(`#${id}-reservation-end`).html(`${reservationInfo.EndTime} (Europe/Berlin)`);
          $(`#${id}-reservation-state`).html(reservationInfo.State);
          $(`#${id}-reservation-details`).html(
            JSON.stringify(reservationInfo, null, 2));
        }
      }
      $(`#${id}-reservation-info-div`).show();
      $(`#${id}-runtime-input`).trigger("change");
    }
    else {
      $(`#${id}-reservation-info-div`).hide();
    }
  });

  $("input[id*=runtime-input").change(function () {

    function _getTimeInMinutes(startTime, endTime){
      const elapsedTime = endTime - startTime;
      const elapsedSeconds = elapsedTime / 1000; // Convert milliseconds to seconds
      const elapsedMinutes = elapsedSeconds / 60; // Convert seconds to minutes
      
      return elapsedMinutes;
    };

    function _resetErrors(id, element) {

      var resourceInfo = getResourceInfo();
      const values = utils.getLabConfigSelectValues(id);
      const partitionResources = ((resourceInfo[values.service] || {})[values.system] || {})[values.partition] || {};
      if (partitionResources.runtime != undefined) {
        let min = (partitionResources.runtime.minmax || [0, 1])[0];
        let max = (partitionResources.runtime.minmax || [0, 1])[1];
        element.siblings(".invalid-feedback").text(`Please choose a number between ${min} and ${max}.`);
      }
      tabWarning.addClass("invisible");
      element.removeClass("is-invalid");
    }

    const id = utils.getId(this);
    const reservationInfo = getReservationInfo();
    const systemReservationInfo = reservationInfo[utils.getLabConfigSelectValues(id)["system"]] || [];
    var tabWarning = $(`#${id}-resources-tab-warning`);
    
    if (reservationInfo) {
      const currentReservation = $(`#${id}-reservation-select`).val();

      if (currentReservation == "None") {
        _resetErrors(id, $(this));
        return;
      }
      for (const reservationInfo of systemReservationInfo) {
        if (reservationInfo.ReservationName == currentReservation) {
          const resStart = reservationInfo.StartTime;
          const resEnd = reservationInfo.EndTime;

          const nowString = Date().toLocaleString("en-US", {timeZone: "Europe/Berlin"});
          const now = new Date(nowString).getTime();
          const reservStart = new Date(resStart).getTime();
          const startTime = (reservStart > now)? reservStart : now;
          const endTime = new Date(resEnd).getTime();

          var reservationTime = _getTimeInMinutes(startTime, endTime);
          var currentRuntimeVal = $(this)[0].value;

          if(currentRuntimeVal > reservationTime){
            // a buffer of 10 minutes, which is used only for the error message to avoid users copy-pasting the maximum time and their job landing in the queue forever
            let buffer = 10;
            const timeLeft = Math.floor(reservationTime - buffer);
            $(this).siblings(".invalid-feedback").text(`Your reservation ends on ${resEnd}. Do not set a runtime which exceeds this limit, e.g., ${timeLeft} minutes.`);
            $(this).addClass("is-invalid");

            tabWarning.removeClass("invisible");
          }
          else {
            _resetErrors(id, $(this));
          }
        }
      }
    }
  });

  $("input.module-selector").click(function () {
    const id = utils.getId(this, -3);
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