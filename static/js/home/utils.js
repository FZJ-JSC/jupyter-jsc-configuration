
define(["jquery"], function ($) {
  "use strict";

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

  var getService = function (options) {
    if ("profile" in options)
      return options["profile"].split('/')[1];
    else
      return options["service"].split('/')[1];
  }

  var resetInputElement = function (element, required = true) {
    element.html("");
    element.val(null);
    element.removeClass("text-muted disabled");
    element.attr("required", required);
  }

  var updateProgressPercentage = function (id, text, progress) {
    var progressBar = $(`#${id}-progress-bar`);
    var progressInfo = $(`#${id}-progress-info-text`);
    progressBar.width(100).html(`<b>${progress}%</b>`);
    progressInfo.html(text);
  }

  var updateProgressState = function (id, text, bg) {
    var progressBar = $(`#${id}-progress-bar`);
    var progressInfo = $(`#${id}-progress-info-text`);
    progressBar
      .width(100)
      .removeClass("bg-success bg-danger")
      .addClass(bg)
      .html("");
    progressInfo.html(text);
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
          var logTimes = $.map(logOptions, function (option) {
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
    getService: getService,
    resetInputElement: resetInputElement,
    updateProgressPercentage: updateProgressPercentage,
    updateProgressState: updateProgressState,
    appendToLog: appendToLog,
    updateSpawnEvents: updateSpawnEvents,
  };

  return utils;
})