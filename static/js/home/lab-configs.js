define(["jquery", "home/utils", "home/dropdown-options"], function (
  $,
  utils,
  dropdowns
) {
  "use strict";

  var checkComputeMaintenance = function (system, partition) {
    const systemInfo = getSystemInfo();
    const interactivePartitions = (systemInfo[system] || {}).interactivePartitions || [];
    if (!interactivePartitions.includes(partition)) {
      const systemUpper = system.replace('-', '').toUpperCase();
      if ((window.systemsHealth[systemUpper] || 0) >= (window.systemsHealth.compute_threshold || 40)) return true;
      else return false;
    }
  }

  var checkIfAvailable = function (id, options) {
    var reason = "due to ";
    var reason_broken_lab = "This lab is broken.\nPlease delete and recreate.";

    // Check if system is not available due to incident
    const systemUpper = options["system"].replace('-', '').toUpperCase();
    if ((window.systemsHealth[systemUpper] || 0) >= (window.systemsHealth.interactive_threshold || 50)) {
      reason += "maintenance";
      utils.setLabAsNA(id, reason);
      return false;
    }

    // Check if system is not available due to groups
    const dropdownOptions = getDropdownOptions();
    const service = getService(options);
    const system = options["system"];
    const account = options["account"];
    const project = options["project"];
    const partition = options["partition"];
    const reservation = options["reservation"];
    const nodes = options["nodes"];
    const runtime = options["runtime"];
    const gpus = options["gpus"];
    const xserver = options["xserver"];

    if (service == undefined) {
      utils.setLabAsNA(id, reason_broken_lab);
      return false;
    }
    if (!(service in dropdownOptions)) {
      reason += "service version";
      utils.setLabAsNA(id, reason);
      return false;
    }
    if (system !== undefined) {
      if (dropdownOptions[service] == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      if (!(system in dropdownOptions[service])) {
        reason += "system";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (account !== undefined) {
      if (dropdownOptions[service][system] == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      if (!(account in dropdownOptions[service][system])) {
        reason += "account";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (project !== undefined) {
      if (dropdownOptions[service][system][account] == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      if (!(project in dropdownOptions[service][system][account])) {
        reason += "project";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (partition !== undefined) {
      if (dropdownOptions[service][system][account][project] == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      if (!(partition in dropdownOptions[service][system][account][project])) {
        reason += "partition";
        utils.setLabAsNA(id, reason);
        return false;
      }
      // Only compute nodes are not available during rolling updates
      if (checkComputeMaintenance(system, partition)) {
        reason += "maintenance";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (reservation !== undefined && reservation != "None") {
      if (dropdownOptions[service][system][account][project][partition] == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      setFalse = true;
      for (const reservation_dict of dropdownOptions[service][system][account][project][partition]) {
        if (reservation == reservation_dict.ReservationName) {
          if (reservation_dict.State == "ACTIVE") {
            setFalse = false;
            break;
          }
        }
      }
      if (setFalse) {
        reason += "reservation";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    // Resources
    const resourceInfo = getResourceInfo();
    const partitionResources = ((resourceInfo[service] || {})[system] || {})[partition] || {};
    if (nodes !== undefined) {
      if (partitionResources.nodes == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      let min = (partitionResources.nodes.minmax || [0, 1])[0];
      let max = (partitionResources.nodes.minmax || [0, 1])[1];
      if (nodes < min || nodes > max) {
        reason += "number of nodes";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (gpus !== undefined) {
      if (partitionResources.gpus == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      let min = (partitionResources.gpus.minmax || [0, 1])[0];
      let max = (partitionResources.gpus.minmax || [0, 1])[1];
      if (gpus < min || gpus > max) {
        reason += "number of GPUs";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (runtime !== undefined) {
      if (partitionResources.runtime == undefined) {
        utils.setLabAsNA(id, reason_broken_lab);
        return false;
      }
      let min = (partitionResources.runtime.minmax || [0, 1])[0];
      let max = (partitionResources.runtime.minmax || [0, 1])[1];
      if (runtime < min || runtime > max) {
        reason += "runtime";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }
    if (xserver !== undefined) {
      if (!("xserver" in partitionResources)) {
        reason += "XServer";
        utils.setLabAsNA(id, reason);
        return false;
      }
    }

    return true;
  }

  var setUserOptions = function (id, options, available) {
    const name = options["name"];
    const service = getService(options);
    const system = options["system"];
    const flavor = options["flavor"];
    const account = options["account"];
    const project = options["project"];
    const partition = options["partition"];
    const reservation = options["reservation"];
    const nodes = options["nodes"];
    const runtime = options["runtime"];
    const gpus = options["gpus"];
    const xserver = options["xserver"];
    const modules = options["userModules"];

    $(`#${id}-name-input`).val(name);
    if (available) {
      /* Set allowed values. Do not rely on change events here as without
          passing a value explicitely, the first allowed option would be 
          chosen regardless of the user option value. */
      try {
        dropdowns.updateService(id, service);
        dropdowns.updateSystems(id, service, system);
        dropdowns.updateFlavors(id, service, system, flavor);
        dropdowns.updateAccounts(id, service, system, account);
        dropdowns.updateProjects(id, service, system, account, project);
        dropdowns.updatePartitions(id, service, system, account, project, partition);
        dropdowns.updateReservation(id, service, system, account, project, partition, reservation);
        dropdowns.updateResources(id, service, system, account, project, partition, nodes, gpus, runtime, xserver);
        dropdowns.updateModules(id, service, system, account, project, partition, modules);
      }
      catch (e) { utils.setLabAsNA(id, "due to a JS error"); }
    }
    else {
      function _setSelectOption(key, value) {
        if (value) $(`#${id}-${key}-select`).append(`<option value="${value}">${value}</option>`);
        dropdowns.updateLabConfigSelect($(`#${id}-${key}-select`), value);
      }

      function _setInputValue(key, value) {
        if (value) $(`#${id}-${key}-input`).val(value);
        else $(`#${id}-${key}-input-div`).hide();
      }

      $(`input[id*=${id}], select[id*=${id}]`).addClass("no-update");

      const serviceInfo = getServiceInfo();
      var serviceName = (serviceInfo.JupyterLab.options[service] || {}).name || service;

      // Selects which are always visible
      $(`#${id}-version-select`).append(`<option value="${service}">${serviceName}</option>`);
      _setSelectOption("system", system);
      _setSelectOption("account", account);
      _setSelectOption("project", project);
      let maintenance = checkComputeMaintenance(system, partition);
      _setSelectOption("partition", maintenance ? `${partition} (in maintenance)` : partition);

      // Reservation
      var hasReservationInfo = false;
      if (reservation) {
        const reservationInfo = getReservationInfo();
        const systemReservationInfo = reservationInfo[system] || [];
        for (const info of systemReservationInfo) {
          if (info.ReservationName == reservation) {
            hasReservationInfo = true;
            var inactive = (info.State == "INACTIVE");
            if (inactive) {
              $(`#${id}-reservation-select`).append(
                `<option value="${reservation}">${reservation} [INACTIVE]</option>`
              );
            }
            else {
              $(`#${id}-reservation-select`).append(
                `<option value="${reservation}">${reservation}</option>`
              );
            }
            $(`#${id}-reservation-select`).trigger("change");
          }
        }
        if (!hasReservationInfo)
          $(`#${id}-reservation-select`).append(`<option value="${reservation}">${reservation}</option>`);
      }
      else {
        $(`#${id}-reservation-select-div`).hide();
        $(`#${id}-reservation-hr`).hide();
      }
      if (hasReservationInfo) $(`#${id}-reservation-info-div`).show()
      else $(`#${id}-reservation-info-div`).hide();

      // Resources
      if ((nodes || runtime || gpus || xserver) !== undefined) {
        _setInputValue("nodes", nodes);
        _setInputValue("runtime", runtime);
        _setInputValue("gpus", gpus);
        // Don't have info about resources, so just never show the xserver checkbox
        _setInputValue("xserver", xserver);
      }
      else {
        $(`#${id}-resources-tab`).addClass("disabled");
      }

      // Modules
      dropdowns.updateModules(id, service, system, account, project, partition, modules);

      // Disable all user input elements if N/A
      $(`input[id*=${id}]`).attr("disabled", true);
      $(`select[id*=${id}]`).not("[id*=log]").addClass("disabled");
    }
  }

  var spawnStatusChanged = function (event) {
    const data = JSON.parse(event.data);
    var spawnEvents = window.spawnEvents;

    // Create eventListeners for new labs if they don't exist
    for (const [id, _] of Object.entries(data)) {
      if (!(id in spawnEvents)) {
        spawnEvents[id] = { "latest": [] };
      }
      if (!(id in evtSources)) {
        utils.updateSpawnEvents(spawnEvents, id);

        let progressUrl = `${window.jhdata.base_url}api/users/${window.jhdata.user}/servers/${id}/progress?_xsrf=${window.jhdata.xsrf_token}`;
        evtSources[id] = new EventSource(progressUrl);
        evtSources[id].onmessage = function (e) {
          onEvtMessage(e, id);
        }
        // Reset progress bar and log for new spawns
        $(`#${id}-progress-bar`)
          .width(0).html("")
          .removeClass("bg-danger bg-success");
        $(`#${id}-progress-info-text`).html("");
        $(`#${id}-log`).html("");
        // Update buttons to reflect pending state
        let tr = $(`tr.summary-tr[data-server-id=${id}]`);
        // _enableTrButtonsRunning
        tr.find(".btn-na-lab, .btn-start-lab").addClass("d-none");
        tr.find(".btn-open-lab, .btn-cancel-lab").removeClass("d-none").addClass("disabled");
      }
    }
  }

  var labConfigs = {
    checkComputeMaintenance: checkComputeMaintenance,
    checkIfAvailable: checkIfAvailable,
    setUserOptions: setUserOptions,
    spawnStatusChanged: spawnStatusChanged,
  }

  return labConfigs;

})