define(["jquery"], function ($) {
  "use strict";

  var updateService = function (id, value) {
    const dropdownOptions = getDropdownOptions();
    const serviceInfo = getServiceInfo();

    let select = $(`select#${id}-version-select`);
    const currentVal = select.val();
    resetInputElement(select);
    for (const service of Object.keys(dropdownOptions).sort().reverse()) {
      var serviceName = (serviceInfo.JupyterLab.options[service] || {}).name || service;
      select.append(`<option value="${service}">${serviceName}</option>`);
    }
    if (!value) value = serviceInfo.JupyterLab.defaultOption;
    updateLabConfigSelect(select, value, currentVal);
  }

  var updateSystems = function (id, service, value) {
    const dropdownOptions = getDropdownOptions();
    const systemInfo = getSystemInfo();

    let select = $(`select#${id}-system-select`);
    const currentVal = select.val();
    resetInputElement(select);

    const systemsAllowed = dropdownOptions[service] || {};
    for (const system of Object.keys(systemInfo).sort((a, b) => (systemInfo[a]["weight"] || 99) < (systemInfo[b]["weight"] || 99) ? -1 : 1)) {
      if (system in systemsAllowed) select.append(`<option value="${system}">${system}</option>`);
    }
    updateLabConfigSelect(select, value, currentVal);
  }

  var updateFlavors = function (id, service, system, value) {
    let select = $(`select#${id}-flavor-select`);
    const currentVal = select.val();

    let systemFlavors = window.flavorInfo[system] || {};
    resetInputElement(select);
    $(`#${id}-flavor-info-div`).html("");

    // Sort systemFlavors by flavor weights
    for (const [flavor, description] of Object.entries(systemFlavors).sort(([, a], [, b]) => (a["weight"] || 99) < (b["weight"] || 99) ? 1 : -1)) {
      var current = description.current;
      var max_allowed = description.max;
      // Flavor not valid, so skip
      if (max_allowed == 0 || current < 0 || max_allowed == null || current == null) continue;
      select.append(`<option value="${flavor}">${description.display_name}</option>`);

      // Infinite allowed
      if (max_allowed == -1) {
        var progress_tooltip = `${current} used`;
        var max_allowed_label = '∞';
        if (current == 0) {
          var current_width = 0;
          var max_allowed_width = 100;
        }
        else {
          var current_width = 20;
          var max_allowed_width = 80;
        }
      }
      else {
        var progress_tooltip = `${current} out of ${max_allowed} used`;
        var max_allowed_label = max_allowed - current;
        var current_width = current / max_allowed * 100 || 0;
        var max_allowed_width = max_allowed_label / max_allowed * 100 || 100;
      }

      var diagramHtml = `
        <div class="row align-items-center g-0 mt-4">
          <div class="col-4">
            <span>${description.display_name}</span>
            <a class="lh-1 ms-3" style="padding-top: 1px;" 
              data-bs-toggle="tooltip" data-bs-placement="right" title="${description.description}">
              ${getInfoSvg()}
            </a>
          </div>
          <div class="progress col ms-2 fw-bold" style="height: 20px;"
            data-bs-toggle="tooltip" data-bs-placement="top" title="${progress_tooltip}">
            <div class="progress-bar" role="progressbar" style="width: ${current_width}%">${current}</div>
            <div class="progress-bar bg-success" role="progressbar" style="width: ${max_allowed_width}%">${max_allowed_label}</div>
          </div>
        </div>
      `
      $(`#${id}-flavor-info-div`).append(diagramHtml);
    }
    enableTooltips();  // Defined in page.html
    Object.keys(systemFlavors).length == 0 ? $(`#${id}-flavor-select-div, #${id}-flavor-legend-div, #${id}-flavor-info-div`).hide() : $(`#${id}-flavor-select-div, #${id}-flavor-legend-div, #${id}-flavor-info-div`).show();
    updateLabConfigSelect(select, value, currentVal);
  }

  var updateAccounts = function (id, service, system, value) {
    const dropdownOptions = getDropdownOptions();

    let select = $(`select#${id}-account-select`);
    const currentVal = select.val();
    resetInputElement(select);

    const accountsAllowed = (dropdownOptions[service] || {})[system] || {};
    for (const account of Object.keys(accountsAllowed).sort()) {
      select.append(`<option value="${account}">${account}</option>`);
    }
    Object.keys(accountsAllowed).length == 0 ? $(`#${id}-account-select-div`).hide() : $(`#${id}-account-select-div`).show();
    updateLabConfigSelect(select, value, currentVal);
  }

  var updateProjects = function (id, service, system, account, value) {
    const dropdownOptions = getDropdownOptions();

    let select = $(`select#${id}-project-select`);
    const currentVal = select.val();
    resetInputElement(select);

    const projectsAllowed = ((dropdownOptions[service] || {})[system] || {})[account] || {};
    for (const project of Object.keys(projectsAllowed).sort()) {
      select.append(`<option value="${project}">${project}</option>`);
    }
    Object.keys(projectsAllowed).length == 0 ? $(`#${id}-project-select-div`).hide() : $(`#${id}-project-select-div`).show();
    updateLabConfigSelect(select, value, currentVal);
  }

  var updatePartitions = function (id, service, system, account, project, value) {
    const dropdownOptions = getDropdownOptions();
    const systemInfo = getSystemInfo();

    let select = $(`select#${id}-partition-select`);
    const currentVal = select.val();
    resetInputElement(select);
    // Distinguish between login and compute nodes
    var loginNodes = [];
    var computeNodes = [];
    const partitionsAllowed = (((dropdownOptions[service] || {})[system] || {})[account] || {})[project] || {};
    const interactivePartitions = (systemInfo[system] || {}).interactivePartitions || [];
    for (const partition of Object.keys(partitionsAllowed).sort()) {
      if (interactivePartitions.includes(partition)) loginNodes.push(partition);
      else computeNodes.push(partition);
    }
    // Append options to select in groups
    if (loginNodes.length > 0) {
      select.append('<optgroup label="Login Nodes">');
      loginNodes.forEach((x) => select.append(`<option value="${x}">${x}</option>`))
      select.append('</optgroup>');
    }
    if (computeNodes.length > 0) {
      select.append('<optgroup label="Compute Nodes">');
      const systemUpper = system.replace('-', '').toUpperCase();
      if ((window.systemsHealth[systemUpper] || 0) >= (window.systemsHealth.threshold.compute || 40)) {
        computeNodes.forEach((x) => select.append(`<option value="${x}" disabled>${x} (in maintenance)</option>`));
      }
      else {
        computeNodes.forEach((x) => select.append(`<option value="${x}">${x}</option>`));
      }
      select.append('</optgroup>');
    }
    Object.keys(partitionsAllowed).length == 0 ? $(`#${id}-partition-select-div`).hide() : $(`#${id}-partition-select-div`).show();
    updateLabConfigSelect(select, value, currentVal);
  }

  var updateReservation = function (id, service, system, account, project, partition, value) {
    const dropdownOptions = getDropdownOptions();
    const reservationInfo = getReservationInfo();

    let select = $(`select#${id}-reservation-select`);
    const currentVal = select.val();
    resetInputElement(select, false);

    const reservationsAllowed = ((((dropdownOptions[service] || {})[system] || {})[account] || {})[project] || {})[partition] || {};
    if (reservationsAllowed.length > 0 && JSON.stringify(reservationsAllowed) !== JSON.stringify(["None"])) {
      for (const reservation of reservationsAllowed) {
        if (reservation == "None") select.append(`<option value="${reservation}">${reservation}</option>`);
        else {
          const reservationName = reservation.ReservationName;
          const systemReservationInfo = reservationInfo[system] || {};
          for (const reservationInfo of systemReservationInfo) {
            if (reservationInfo.ReservationName == reservationName) {
              if (reservationInfo.State == "ACTIVE") select.append(`<option value="${reservationName}">${reservationName}</option>`);
              else select.append(`<option value="${reservationName}" disabled style="color: #6c757d;">${reservationName} [INACTIVE]</option>`);
            }
          }
        }
      }
      select.attr("required", true);
      $(`#${id}-reservation-select-div`).show();
      $(`#${id}-reservation-hr`).show();
    }
    else {
      $(`#${id}-reservation-select-div`).hide();
      $(`#${id}-reservation-hr`).hide();
    }
    updateLabConfigSelect(select, value, currentVal);
  }

  var updateResources = function (id, service, system, account, project, partition, nodes, gpus, runtime, xserver) {
    const resourceInfo = getResourceInfo();
    let nodesInput = $(`input#${id}-nodes-input`);
    let gpusInput = $(`input#${id}-gpus-input`);
    let runtimeInput = $(`input#${id}-runtime-input`);
    let xserverCheckboxInput = $(`input#${id}-xserver-cb-input`);
    let xserverInput = $(`input#${id}-xserver-input`);
    let tabWarning = $(`#${id}-resources-tab-warning`);
    const currentNodeVal = nodesInput.val();
    const currentGpusVal = gpusInput.val();
    const currentRuntimeVal = runtimeInput.val();
    const currentXserverCbVal = xserverCheckboxInput[0].checked;
    const currentXserverVal = xserverInput.val();
    [nodesInput, gpusInput, runtimeInput, xserverInput].forEach(input => resetInputElement(input, false));
    xserverCheckboxInput[0].checked = false;

    const systemResources = (resourceInfo[service] || {})[system] || {};
    if ($.isEmptyObject(systemResources)) {
      $(`#${id}-resources-tab`).addClass("disabled");
      tabWarning.addClass("invisible");
    }
    else {
      const partitionResources = systemResources[partition];
      if ($.isEmptyObject(partitionResources)) {
        $(`#${id}-resources-tab`).addClass("disabled");
        tabWarning.addClass("invisible");
      }
      else {
        $(`#${id}-resources-tab`).removeClass("disabled");
        if ("nodes" in partitionResources) {
          let min = (partitionResources.nodes.minmax || [0, 1])[0];
          let max = (partitionResources.nodes.minmax || [0, 1])[1];
          $(`label[for*=${id}-nodes-input]`).text("Nodes [" + min + "," + max + "]");
          let defaultNodes = partitionResources.nodes.default || 0;
          updateLabConfigInput(nodesInput, nodes, currentNodeVal, min, max, defaultNodes);
          $(`#${id}-nodes-input-div`).show();
          if (!currentNodeVal) tabWarning.removeClass("invisible");
        }
        else {
          $(`#${id}-nodes-input-div`).hide();
          if (currentNodeVal) tabWarning.removeClass("invisible");
        }

        if ("gpus" in partitionResources) {
          let min = (partitionResources.gpus.minmax || [0, 1])[0];
          let max = (partitionResources.gpus.minmax || [0, 1])[1];
          $(`label[for*=${id}-gpus-input]`).text("GPUs [" + min + "," + max + "]");
          let defaultGpus = partitionResources.gpus.default || 0;
          updateLabConfigInput(gpusInput, gpus, currentGpusVal, min, max, defaultGpus);
          $(`#${id}-gpus-input-div`).show();
          if (!currentGpusVal) tabWarning.removeClass("invisible");
        }
        else {
          $(`#${id}-gpus-input-div`).hide();
          if (currentGpusVal) tabWarning.removeClass("invisible");
        }

        if ("runtime" in partitionResources) {
          let min = (partitionResources.runtime.minmax || [0, 1])[0];
          let max = (partitionResources.runtime.minmax || [0, 1])[1];
          $(`label[for*=${id}-runtime-input]`).text("Runtime (minutes) [" + min + "," + max + "]");
          let defaultRuntime = partitionResources.runtime.default || 0;
          updateLabConfigInput(runtimeInput, runtime, currentRuntimeVal, min, max, defaultRuntime);
          $(`#${id}-runtime-input-div`).show();
          if (!currentRuntimeVal) tabWarning.removeClass("invisible");
        }
        else {
          $(`#${id}-runtime-input-div`).hide();
          if (currentRuntimeVal) tabWarning.removeClass("invisible");
        }

        if ("xserver" in partitionResources) {
          let cblabel = partitionResources.xserver.cblabel || "Activate XServer";
          $(`label[for*=${id}-xserver-cb-input]`).text(cblabel);
          var min = (partitionResources.xserver.minmax || [0, 1])[0];
          var max = (partitionResources.xserver.minmax || [0, 1])[1];
          let label = partitionResources.xserver.label || "Use XServer GPU Index";
          $(`label[for*=${id}-xserver-input]`).text(label + " [" + min + "," + max + "]");

          if (xserver) { xserverCheckboxInput[0].checked = true; }
          else {
            xserver = partitionResources.xserver.default || 0;
            if (!currentXserverVal) tabWarning.removeClass("invisible");
            // Determine if XServer checkbox should be shown
            if (partitionResources.xserver.checkbox || false) {
              $(`#${id}-xserver-cb-input-div`).show();
              if (currentXserverCbVal) xserverCheckboxInput[0].checked = true;
              else {
                if (partitionResources.xserver.default_checkbox || false)
                  xserverCheckboxInput[0].checked = true;
                else xserverCheckboxInput[0].checked = false;
              }
              if (!currentXserverCbVal && xserverCheckboxInput[0].checked) tabWarning.removeClass("invisible");
            }
            else {
              $(`#${id}-xserver-cb-input-div`).hide();
              xserverCheckboxInput[0].checked = true;
              if (!currentXserverCbVal) tabWarning.removeClass("invisible");
            }
          }
          updateLabConfigInput(xserverInput, xserver, currentXserverVal, min, max);
          if (xserverCheckboxInput[0].checked) $(`#${id}-xserver-input-div`).show();
          else $(`#${id}-xserver-input-div`).hide();
        }
        else {
          $(`#${id}-xserver-cb-input-div`).hide();
          $(`#${id}-xserver-input-div`).hide();
          if (currentXserverCbVal || currentXserverVal) tabWarning.removeClass("invisible");
        }
      }
    }
  }

  var updateModules = function updateModules(id, service, system, account, project, partition, values) {
    const moduleInfo = getModuleInfo();
    const systemInfo = getSystemInfo();
    const interactivePartitions = (systemInfo[system] || {}).interactivePartitions || [];

    var tabWarning = $(`#${id}-modules-tab-warning`);
    var currentOptions = [];
    $(`#${id}-modules-form`).find(`input[type=checkbox]`).each(function () {
      currentOptions.push($(this).val());
    })

    var defaultOptions = [];
    var enableModulesTab = false;

    for (const [moduleSet, modules] of Object.entries(moduleInfo)) {
      $(`#${id}-${moduleSet}-div`).hide();
      var insertIndex = -1;
      for (const [module, moduleInfo] of Object.entries(modules)) {
        if (moduleInfo.sets.includes(service)) {
          if (moduleInfo.allowedSystems && !moduleInfo.allowedSystems.includes(system)) {
            // Module not in allowed systems, so do nothing.
          }
          else {
            if (moduleInfo.compute_only && interactivePartitions.includes(partition)) {
              // Module is compute only, but partition is interactive, so do nothing.
            }
            else {
              $(`#${id}-${moduleSet}-div`).show();
              enableModulesTab = true;
              defaultOptions.push(module);
              // If checkbox already exists, do nothing
              // Else create it and set the default value
              if (!currentOptions.includes(module)) {
                let parent = $(`#${id}-${moduleSet}-checkboxes-div`);
                let checked = moduleInfo.default ? "checked" : "";
                let module_cols = "col-sm-6 col-md-4 col-lg-3";
                let cbHtml = `
                  <div id="${id}-${module}-cb-div" class="form-check ${module_cols}">
                    <input type="checkbox" class="form-check-input" id="${id}-${module}-check" value="${module}" ${checked}>
                      <label class="form-check-label" for="${id}-${module}-check">
                        <span class="align-middle">${moduleInfo.displayName}</span>
                        <a href="${moduleInfo.href}" target="_blank" class="module-info text-muted ms-3">
                          <span>${getInfoSvg()}</span>
                            <div class="module-info-link-div d-inline-block">
                              <span class="module-info-link" id="${module}-info-link">
                                ${getLinkSvg()}
                              </span>
                            </div>
                        </a>
                      </label>
                    </input>
                  </div>
                `
                // No checkboxes exist yet, so we can simply append to the parent div
                if (parent.children().length == 0) {
                  parent.append(cbHtml);
                }
                // Otherwise, we need to determine where to insert the new checkbox
                else {
                  // Get the current element at index
                  var target = parent.children().eq(insertIndex);
                  target.before(cbHtml);
                }
                // Show tab warning to indicate changes in checkbox options
                tabWarning.removeClass("invisible");
              }
              insertIndex++;
            }
          }
        }
      }
    }
    // Remove checkboxes which still exist but should not anymore
    var shouldRemove = currentOptions.filter(x => !defaultOptions.includes(x));
    for (const module of shouldRemove) {
      $(`#${id}-${module}-cb-div`).remove();
      // Show tab warning to indicate changes in checkbox options
      tabWarning.removeClass("invisible");
    }

    // Set values according to previous values.
    if (values) {
      // Loop through all checkboxes and only check those in values.
      $(`#${id}-modules`).find("input[type=checkbox]").each((i, cb) => {
        if (values.includes(cb.value)) cb.checked = true;
        else cb.checked = false;
      })
    }

    if (enableModulesTab) $(`#${id}-modules-tab`).removeClass("disabled");
    else {
      $(`#${id}-modules-tab`).addClass("disabled");
      tabWarning.addClass("invisible");
    }
  }

  /*
  Util functions
  */
  var resetInputElement = function (element, required = true) {
    element.html("");
    element.val(null);
    element.removeClass("text-muted disabled");
    element.attr("required", required);
  }

  var updateLabConfigSelect = function (select, value, lastSelected) {
    // For some systems, e.g. cloud, some options are not available
    if (select.html() == "") {
      select.append("<option disabled>Not available</option>");
      select.addClass("text-muted").removeAttr("required");
    }
    // If there is only one option, we disable the dropdown
    const numberOfOptions = select.children().length
    if (numberOfOptions == 1) {
      select.addClass("disabled");
    }
    if (value) select.val(value);
    else {
      // Check if the last value is contained in the new options,
      // otherwise just select the first value.
      var index = 0;
      select.children().each(function (i, option) {
        if ($(option).val() == lastSelected) {
          index = i;
          /* Although index should be used to set the value and
            avoid the (index == 0) query, indices don't work directly
            when there are optiongroups in the select. So we set
            it via the .val() function regardless. */
          select.val(lastSelected);
          return;
        }
      })
      if (index == 0) select.prop("selectedIndex", index);
    }
    select[0].dispatchEvent(new Event("change"));
  }

  var updateLabConfigInput = function (input, value, lastSelected, min, max, defaultValue) {
    input.attr({ "min": min, "max": max });
    input.attr("required", true);
    // Set message for invalid feedback
    input.siblings(".invalid-feedback")
      .text(`Please choose a number between ${min} and ${max}.`);
    if (value) {
      input.val(value);
    }
    // Check if we can keep the old value
    else if (lastSelected != "" && lastSelected >= min && lastSelected <= max) {
      input.val(lastSelected);
    }
    else {
      input.val(defaultValue);
    }
  }

  var updateDropdowns = {
    updateService: updateService,
    updateSystems: updateSystems,
    updateFlavors: updateFlavors,
    updateAccounts: updateAccounts,
    updateProjects: updateProjects,
    updatePartitions: updatePartitions,
    updateReservation: updateReservation,
    updateResources: updateResources,
    updateModules: updateModules,
    resetInputElement: resetInputElement,
    updateLabConfigSelect: updateLabConfigSelect,
    updateLabConfigInput: updateLabConfigInput,
  }

  return updateDropdowns;

})