// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi", "utils"], function (
  $,
  JHAPI,
  utils,
) {
  "use strict";

  var base_url = window.jhdata.base_url;
  var user = window.jhdata.user;
  var api = new JHAPI(base_url);

  function cancelServer() {
    var tr = _getTr(this);
    const id = tr.data("server-id");
    _disableTrButtons(tr);
    api.cancel_named_server(user, id, {
      success: function () {
        console.log("cancel success");
        // If cancelling, we want to keep to keep the
        // progress indicator,so we do not reset the progress bar
      },
      error: function () {
        console.log("cancel error");
      }
    });
  }

  function stopServer() {
    var tr = _getTr(this);
    const id = tr.data("server-id");
    _disableTrButtons(tr);
    $(`#${id}-progress-bar`).removeClass("bg-success").addClass("bg-danger");
    $(`#${id}-progress-info-text`).html("stopping...");
    api.stop_named_server(user, id, {
      success: function () {
        console.log("stop success");
        _enableTrButtonsNonRunning(tr);
        _resetProgress(id);
      },
      error: function (xhr) {
        console.log("stop error");
        tr.find(".btn-open-lab, .btn-cancel-lab").removeClass("disabled");
        $(`#${id}-progress-bar`).removeClass("bg-danger").addClass("bg-success");
        $(`#${id}-progress-info-text`).html("running (stop failed)");
        $(`#${id}-log`)
          .append($('<div class="log-div">')
            .html`Could not stop server. Error: ${xhr.responseText}`);
      }
    });
  }

  function deleteServer() {
    var collapsibleTr = _getTr(this);
    var that = $(this);
    const id = collapsibleTr.data("server-id");
    _disableTrButtons(collapsibleTr);
    api.delete_named_server(user, id, {
      success: function () {
        $(`tr[data-server-id=${id}]`).each(function () {
          $(this).remove();
        })
      },
      error: function (xhr) {
        var alert = that.siblings(".alert");
        const displayName = _getDisplayName(collapsibleTr);
        _showErrorAlert(alert, displayName, xhr.responseText);
      }
    });
  }

  function startServer() {
    var tr = _getTr(this);
    const id = tr.data("server-id");
    var collapsibleTr = tr.siblings(`.collapsible-tr[data-server-id=${id}]`);

    _disableTrButtons(tr);
    // Validate the form and start spawn only after validation
    try {
      $(`form[id*=${id}]`).submit();
    }
    catch (e) {
      _enableTrButtonsNonRunning(tr);
      return;
    }

    // Set the href of the start button to the spawn url
    _resetProgress(id);
    $(`#${id}-log`).html("");

    var options = _createDataDict(collapsibleTr);
    // Update the summary row according to the values set in the collapsibleTr
    _updateTr(tr, id, options);
    // Open a new tab for spawn_pending.html
    // Need to create it here for context reasons
    var newTab = window.open("about:blank");
    api.start_named_server(user, id, {
      data: JSON.stringify(options),
      success: function () {
        // Save latest log to time stamp and empty it
        _updateSpawnEventsAndLog(id);
        // Update global user options
        userOptions[id] = options;
        // Open the spawn url in the new tab
        newTab.location.href = utils.url_path_join(base_url, "spawn", user, id);
        // Hook up event-stream for progress
        if (!(id in evtSources)) {
          var progressUrl = utils.url_path_join(jhdata.base_url, "api/users", jhdata.user, "servers", id, "progress");
          progressUrl = progressUrl + "?_xsrf=" + window.jhdata.xsrf_token;
          evtSources[id] = new EventSource(progressUrl);
          evtSources[id].onmessage = function (e) {
            onEvtMessage(e, id);
          }
        }
        // Successfully sent request to start the lab, enable row again
        _enableTrButtonsRunning(tr);
      },
      error: function (xhr) {
        newTab.close();
        // If cookie is not valid anymore, refresh the page.
        // This should redirect the user to the login page.
        if (xhr.status == 403) {
          document.location.reload();
          return;
        }
        // Update progress in tr
        $(`#${id}-progress-bar`)
          .width(100)
          .removeClass(".bg-success")
          .addClass(".bg-danger");
        $(`#${id}-progress-info-text`).html("last spawn failed");
        // Update progress in log
        let details = $("<details>")
          .append($("<summary>")
            .html(`Could not request spawn. Error: ${xhr.responseText}`))
          .append($("<pre>")
            .html(_parseJSON(xhr.responseText)));
        let div = $("<div>").addClass("log-div").html(details);
        $(`#${id}-log`).append(div);
        // Spawn attempt finished, enable row again
        _enableTrButtonsNonRunning(tr);
      }
    });
  }

  function startNewServer() {
    function uuidv4hex() {
      return ([1e7, 1e3, 4e3, 8e3, 1e11].join('')).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
    }

    function uuidWithLetterStart() {
      let uuid = uuidv4hex();
      let char = Math.random().toString(36).match(/[a-zA-Z]/)[0];
      return char + uuid.substring(1);
    }

    const id = "new_jupyterlab";
    const uuid = uuidWithLetterStart();
    // Start button is in collapsible tr for new labs
    var collapsibleTr = _getTr(this);
    _disableTrButtons(collapsibleTr);

    // Validate the form and start spawn only after validation
    try {
      $(`form[id*=${id}]`).submit();
    }
    catch (e) {
      collapsibleTr.find("button").removeClass("disabled");
      return;
    }

    var options = _createDataDict(collapsibleTr);
    // Open a new tab for spawn_pending.html
    // Need to create it here for context reasons
    var newTab = window.open("about:blank");
    api.start_named_server(user, uuid, {
      data: JSON.stringify(options),
      success: function () {
        var url = utils.url_path_join(base_url, "spawn", user, uuid);
        newTab.location.href = url;
        // Reload page to add spawner to table
        location.reload();
      },
      error: function (xhr) {
        newTab.close();
        // If cookie is not valid anymore, refresh the page.
        // This should redirect the user to the login page.
        if (xhr.status == 403) {
          document.location.reload();
          return;
        }
        // Show information about why the start failed
        let details = $("<details>")
          .append($("<summary>")
            .html(`Could not request spawn. Error: ${xhr.responseText}`))
          .append($("<pre>")
            .html(_parseJSON(xhr.responseText)));
        let div = $("<div>").addClass("log-div").html(details);
        $(`#${id}-log`).append(div);
        collapsibleTr.find("button").removeClass("disabled");
      }
    });
  }

  $(".btn-start-lab").click(startServer);
  $(".btn-start-new-lab").click(startNewServer);
  $(".btn-cancel-lab").click(cancelServer);
  $(".btn-stop-lab").click(stopServer);
  $(".btn-delete-lab").click(deleteServer);


  /*
  Validate form before starting a new lab
  */
  $("form").submit(function (event) {
    event.preventDefault();
    event.stopPropagation();

    if (!$(this)[0].checkValidity()) {
      $(this).addClass('was-validated');
      // Show the tab where the error was thrown
      var tab_id = $(this).attr("id").replace("-form", "-tab");
      var tab = new bootstrap.Tab($("#" + tab_id));
      tab.show();
      // Open the collapsibleTr if it was hidden
      const id = getId(this);
      var tr = $(`.summary-tr[data-server-id=${id}`);
      if (!$(`${id}-collapse`).css("display") == "none") {
        tr.trigger("click");
      }
      throw {
        name: "FormValidationError",
        toString: function () {
          return this.name;
        }
      };
    } else {
      $(this).removeClass('was-validated');
    }
  });


  /*
  Save and revert changes to spawner
  */
  function saveChanges() {
    var collapsibleTr = _getTr(this);
    const id = getId(this);
    var tr = $(`.summary-tr[data-server-id=${id}]`);
    var alert = $(this).siblings(".alert");

    const displayName = _getDisplayName(collapsibleTr);
    const options = _createDataDict(collapsibleTr);
    api.update_named_server(user, id, {
      data: JSON.stringify(options),
      success: function () {
        _updateTr(tr, id, options);
        // Update global user options
        userOptions[id] = options;
        alert.children("span")
          .text(`Successfully updated ${displayName}.`);
        alert
          .removeClass("alert-danger p-0")
          .addClass("alert-success show p-1");
      },
      error: function (xhr) {
        _showErrorAlert(alert, displayName, xhr.responseText);
      }
    });
  }

  function revertChanges() {
    const id = getId(this);
    var alert = $(this).siblings(".alert");

    const options = userOptions[id];
    if (options) var name = options["name"];
    else var name = "new JupyterLab";

    api.update_named_server(user, id, {
      data: JSON.stringify(options),
      success: function () {
        $(`#${id}-name-input`).val(options["name"]);
        // Reset all user inputs to the values saved in the global user options
        setUserOptions(id, options);
        // Remove all tab warnings since manual changes shouldn't cause warnings
        $("[id$=tab-warning]").addClass("invisible");
        // Show first tab after resetting values
        var trigger = $(`#${id}-collapse`).find(".nav-link").first();
        var tab = new bootstrap.Tab(trigger);
        tab.show();
        alert.children("span")
          .text(`Successfully reverted settings for ${name}.`);
        alert
          .removeClass("alert-danger p-0")
          .addClass("alert-success show p-1");
      },
      error: function (xhr) {
        _showErrorAlert(alert, displayName, xhr.responseText);
      }
    });
  }

  $(".btn-save-lab").click(saveChanges);
  $(".btn-reset-lab").click(revertChanges);

  /*
  Util functions
  */
  function _getDisplayName(collapsibleTr) {
    var displayName = collapsibleTr.find("input[id*=name]").val();
    if (displayName == "") displayName = "Unnamed JupyterLab";
    return displayName;
  }

  function _getTr(element) {
    return $(element).parents("tr");
  }

  function _disableTrButtons(tr) {
    // Disable buttons
    tr.find(".btn").addClass("disabled");
  }

  function _enableTrButtonsRunning(tr) {
    // Show open/cancel for starting labs
    tr.find(".btn-na-lab, .btn-start-lab").addClass("d-none");
    tr.find(".btn-open-lab, .btn-cancel-lab").removeClass("d-none");
    // Disable until fitting event received from EventSource
    tr.find(".btn-open-lab, .btn-cancel-lab").addClass("disabled");
  }

  function _enableTrButtonsNonRunning(tr) {
    var na = tr.find(".na-status").text() || 0;
    // Show start or na for non-running labs
    if (na != "0") {
      tr.find(".btn-na-lab").removeClass("d-none disabled");
      tr.find(".btn-start-lab").addClass("d-none");
    }
    else {
      tr.find(".btn-na-lab").addClass("d-none")
      tr.find(".btn-start-lab").removeClass("d-none disabled");
    }
    tr.find(".btn-open-lab, .btn-cancel-lab, .btn-stop-lab").addClass("d-none");
  }

  function _resetProgress(id) {
    let progressBar = $(`#${id}-progress-bar`);
    let infoText = $(`#${id}-progress-info-text`);
    progressBar.width(0).html("");
    progressBar.removeClass("bg-danger bg-success");
    infoText.html("");
  }

  function _showErrorAlert(alert, name, text) {
    alert.children("span")
      .text(`Could not update ${name}. Error: ${text}`);
    alert
      .removeClass("alert-success p-0")
      .addClass("alert-danger show p-1");
  }

  function _parseJSON(inputString) {
    try {
      return JSON.stringify(JSON.parse(inputString), null, 2);
    } catch (e) {
      return inputString;
    }
  }

  function _createDataDict(collapsibleTr) {
    var options = {}
    options["name"] = _getDisplayName(collapsibleTr);

    function _addSelectValue(param) {
      var select = collapsibleTr.find(`select[id*=${param}]`);
      var value = select.val();
      if (param == "version") {
        param = "service"
        value = "JupyterLab/" + value;
      }
      if (value) options[param] = value;
    }

    function _addInputValue(param) {
      var input = collapsibleTr.find(`input[id*=${param}]`);
      var value = input.val();
      if (param == "xserver") {
        if (!collapsibleTr.find(`input[id*=xcbserver-input]`)[0].checked) return;
      }
      if (value) options[param] = value;
    }

    function _addCbValues(param) {
      var checkboxes = collapsibleTr
        .find('form[id*=modules-form]')
        .find(`input[type=checkbox]`);
      var values = [];
      checkboxes.each(function () {
        if (this.checked) values.push($(this).val());
      });
      options[param] = values;
    }

    _addSelectValue("version"); // service
    _addSelectValue("system");
    _addSelectValue("flavor");
    _addSelectValue("account");
    _addSelectValue("project");
    _addSelectValue("partition");
    _addSelectValue("reservation");
    _addInputValue("nodes");
    _addInputValue("gpus");
    _addInputValue("runtime");
    _addInputValue("xserver");
    _addCbValues("userModules");
    return options;
  }

  function _updateTr(tr, id, options) {
    tr.find(".name-td").text(options.name);
    tr.find(`#${id}-config-td-system`).text(options.system);
    tr.find(`#${id}-config-td-flavor`).text(options.flavor);
    tr.find(`#${id}-config-td-partition`).text(options.partition);
    tr.find(`#${id}-config-td-project`).text(options.project);
    tr.find(`#${id}-config-td-runtime`).text(options.runtime / 60);
    tr.find(`#${id}-config-td-nodes`).text(options.nodes);
    tr.find(`#${id}-config-td-gpus`).text(options.gpus);
  }

  function _updateSpawnEventsAndLog(id) {
    const startEvent = spawnEvents[id]["latest"][0];
    if (startEvent) {
      const startMsg = startEvent.html_message;
      var re = /([0-9]+(_[0-9]+)+).*[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,3})?/;
      var startTime = re.exec(startMsg)[0];
      spawnEvents[id][startTime] = spawnEvents[id]["latest"];
      spawnEvents[id]["latest"] = [];
      $(`#${id}-log-select`)
        .append(`<option value="${startTime}">${startTime}</option>`)
        .val("latest");
    }
  }
});
