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

  var utils = {
    parseJSON: parseJSON,
    getId: getId,
    getLabConfigSelectValues: getLabConfigSelectValues,
    setLabAsNA: setLabAsNA,
    updateProgressState: updateProgressState,
    appendToLog: appendToLog,
    updateSpawnEvents: updateSpawnEvents,
  };

  return utils;
})