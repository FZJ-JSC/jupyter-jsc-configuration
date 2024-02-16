define(["jquery"], function ($) {
  "use strict";

  const progressStates = {
    "running": {
      "text": "running",
      "background": "bg-success",
      "width": 100
    },
    "stop_failed": {
      "text": "running (stop failed)",
      "background": "bg-success",
      "width": 100
    },
    "cancelling": {
      "text": "cancelling...",
      "background": "bg-danger",
      "width": 100
    },
    "stopping": {
      "text": "stopping...",
      "background": "bg-danger",
      "width": 100
    },
    "failed": {
      "text": "last spawn failed",
      "background": "bg-danger",
      "width": 100
    },
    "reset": {
      "text": "",
      "background": "",
      "width": 0
    }
  }

  var parseJSON = function (inputString) {
    try {
      return JSON.stringify(JSON.parse(inputString), null, 2);
    } catch (e) {
      return inputString;
    }
  }

  var getId = function (element, slice_index = -2) {
    let id_array = $(element).attr("id").split('-');
    let id = id_array.slice(0, slice_index).join('-');
    return id;
  }

  var getLabConfigSelectValues = function (id) {
    return {
      "service": $(`select#${id}-version-select`).val(),
      "system": $(`select#${id}-system-select`).val(),
      "flavor": $(`select#${id}-flavor-select`).val(),
      "account": $(`select#${id}-account-select`).val(),
      "project": $(`select#${id}-project-select`).val(),
      "partition": $(`select#${id}-partition-select`).val(),
    }
  }

  var setLabAsNA = function (id, reason) {
    $(`#${id}-start-btn, #${id}-open-btn, #${id}-cancel-btn, #${id}-stop-btn`).addClass("disabled").hide();
    $(`#${id}-na-btn`).show();
    $(`#${id}-na-status`).html(1);
    $(`#${id}-na-info`).html(reason).show();
  }

  var setSpawnActive = function (id, active) {
    window.spawnActive[id] = active;
  }

  var updateProgressState = function (id, state) {
    $(`#${id}-progress-bar`)
      .width(progressStates[state].width)
      .removeClass("bg-success bg-danger")
      .addClass(progressStates[state].background)
      .html("");
    $(`#${id}-progress-info-text`).html(progressStates[state].text);
  }

  var appendToLog = function (log, htmlMsg) {
    try { htmlMsg = htmlMsg.replace(/&nbsp;/g, ' '); }
    catch (e) { return; } // Not a valid htmlMsg
    // Only append if a log message has not been appended yet
    var exists = false;
    log.children().each(function (i, e) {
      let logMsg = $(e).html();
      if (htmlMsg == logMsg) exists = true;
    })
    if (!exists)
      log.append($('<div class="log-div">').html(htmlMsg));
  }

  var updateSpawnEvents = function (spawnEvents, id) {
    if (spawnEvents[id]["latest"].length) {
      var re = /([0-9]+(-[0-9]+)+).*[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,3})?/;
      for (const [_, event] of spawnEvents[id]["latest"].entries()) {
        const startMsg = event.html_message || event.message;
        const startTimeMatch = re.exec(startMsg);
        if (startTimeMatch) {
          const startTime = startTimeMatch[0];
          // Have we already created a log entry for this time?
          let logOptions = $(`#${id}-log-select option`);
          let logTimes = $.map(logOptions, function (option) {
            return option.value;
          });
          // If yes, we do not need to do anything anymore
          if (logTimes.includes(startTime)) return;
          // Otherwise, save the current events to the startTime,
          // update the log select and reset the "latest" events.
          spawnEvents[id][startTime] = spawnEvents[id]["latest"];
          spawnEvents[id]["latest"] = [];
          $(`#${id}-log-select`)
            .append(`<option value="${startTime}">${startTime}</option>`)
            .val("latest");
          break;
        }
      }
      // We didn't manage to find a time, so update with no timestamp
      if ((spawnEvents[id]["latest"].length)) {
        spawnEvents[id]["previous"] = spawnEvents[id]["latest"];
        spawnEvents[id]["latest"] = [];
      }
    }
  }

  var createFlavorInfo = function (id, system) {
    const systemFlavors = window.flavorInfo[system] || {};
    for (const [_, description] of Object.entries(systemFlavors).sort(([, a], [, b]) => (a["weight"] || 99) < (b["weight"] || 99) ? 1 : -1)) {
      var current = description.current || 0;
      var maxAllowed = description.max;
      // Flavor not valid, so skip
      if (maxAllowed == 0 || current < 0 || maxAllowed == null || current == null) continue;

      var bgColor = "bg-primary";
      // Infinite allowed
      if (maxAllowed == -1) {
        var progressTooltip = `${current} used`;
        var maxAllowedLabel = '∞';
        if (current == 0) {
          var currentWidth = 0;
          var maxAllowedWidth = 100;
        }
        else {
          var currentWidth = 20;
          var maxAllowedWidth = 80;
        }
      }
      else {
        var progressTooltip = `${current} out of ${maxAllowed} used`;
        var maxAllowedLabel = maxAllowed - current;
        var currentWidth = current / maxAllowed * 100;
        var maxAllowedWidth = maxAllowedLabel / maxAllowed * 100;

        if (maxAllowedLabel < 0) {
          maxAllowedLabel = 0;
          maxAllowedWidth = 0;
          bgColor = "bg-danger";
        }
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
            data-bs-toggle="tooltip" data-bs-placement="top" title="${progressTooltip}">
            <div class="progress-bar ${bgColor}" role="progressbar" style="width: ${currentWidth}%">${current}</div>
            <div class="progress-bar bg-success" role="progressbar" style="width: ${maxAllowedWidth}%">${maxAllowedLabel}</div>
          </div>
        </div>
      `
      $(`#${id}-flavor-info-div`).append(diagramHtml);
    }
  }

  var utils = {
    parseJSON: parseJSON,
    getId: getId,
    getLabConfigSelectValues: getLabConfigSelectValues,
    setLabAsNA: setLabAsNA,
    setSpawnActive: setSpawnActive,
    updateProgressState: updateProgressState,
    appendToLog: appendToLog,
    updateSpawnEvents: updateSpawnEvents,
    createFlavorInfo: createFlavorInfo,
  };

  return utils;
})