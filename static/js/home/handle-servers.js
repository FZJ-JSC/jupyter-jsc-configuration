// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi", "utils", "home/utils"], function (
  $,
  JHAPI,
  utils,
  custom_utils
) {
  "use strict";

  var base_url = window.jhdata.base_url;
  var user = window.jhdata.user;
  var api = new JHAPI(base_url);

  function cancelServer() {
    var [tr, id] = _getTrAndId(this);
    _disableTrButtons(tr);
    api.cancel_named_server(user, id, {
      success: function () {
        console.log("cancel success");
      },
      error: function () {
        console.log("cancel error");
      }
    });
  }

  function stopServer() {
    var [tr, id] = _getTrAndId(this);
    _disableTrButtons(tr);
    custom_utils.updateProgressState(id, "stopping");
    api.stop_named_server(user, id, {
      success: function () {
        console.log("stop success");
        let running = false;
        _enableTrButtons(tr, running);
        // Reset progress
        custom_utils.updateProgressState(id, "reset");
      },
      error: function (xhr) {
        console.log("stop error");
        custom_utils.updateProgressState(id, "stop_failed");
        tr.find(".btn-open-lab, .btn-cancel-lab").removeClass("disabled");
        $(`#${id}-log`)
          .append($('<div class="log-div">')
            .html`Could not stop server. Error: ${xhr.responseText}`);
      }
    });
  }

  function deleteServer() {
    var that = $(this);
    var [collapsibleTr, id] = _getTrAndId(this);
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
    var [tr, id] = _getTrAndId(this);
    var collapsibleTr = tr.siblings(`.collapsible-tr[data-server-id=${id}]`);
    _disableTrButtons(tr);

    // Validate the form and start spawn only after validation
    try {
      $(`form[id*=${id}]`).submit();
    }
    catch (e) {
      let running = false;
      _enableTrButtons(tr, running);
      return;
    }
    custom_utils.updateProgressState(id, "reset");
    $(`#${id}-log`).html("");

    var options = _createDataDict(collapsibleTr);
    // Update the summary row according to the values set in the collapsibleTr
    _updateTr(tr, id, options);
    // Open a new tab for spawn_pending.html
    // Need to create it here for JS context reasons
    var newTab = window.open("about:blank");
    api.start_named_server(user, id, {
      data: JSON.stringify(options),
      success: function () {
        // Save latest log to time stamp and empty it
        custom_utils.updateSpawnEvents(window.spawnEvents, id);
        window.userOptions[id] = options;
        // Open the spawn url in the new tab
        newTab.location.href = utils.url_path_join(base_url, "spawn", user, id);
        // Hook up event-stream for progress
        var evtSources = window.evtSources;
        if (!(id in evtSources)) {
          var progressUrl = utils.url_path_join(jhdata.base_url, "api/users", jhdata.user, "servers", id, "progress");
          progressUrl = progressUrl + "?_xsrf=" + window.jhdata.xsrf_token;
          evtSources[id] = new EventSource(progressUrl);
          evtSources[id].onmessage = function (e) {
            onEvtMessage(e, id);
          }
        }
        // Successfully sent request to start the lab, enable row again
        let running = true;
        _enableTrButtons(tr, running);
      },
      error: function (xhr) {
        newTab.close();
        // If cookie is not valid anymore, refresh the page.
        // This should redirect the user to the login page.
        if (xhr.status == 403) {
          document.location.reload();
          return;
        }
        custom_utils.updateProgressState(id, "failed");
        // Update progress in log
        let details = $("<details>")
          .append($("<summary>")
            .html(`Could not request spawn. Error: ${xhr.responseText}`))
          .append($("<pre>")
            .html(custom_utils.parseJSON(xhr.responseText)));
        $(`#${id}-log`).append(
          $("<div>").addClass("log-div").html(details)
        );
        // Spawn attempt finished, enable row again
        let running = false;
        _enableTrButtons(tr, running);
      }
    });
  }

  function startNewServer() {
    function _uuidv4hex() {
      return ([1e7, 1e3, 4e3, 8e3, 1e11].join('')).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
    }

    function _uuidWithLetterStart() {
      let uuid = _uuidv4hex();
      let char = Math.random().toString(36).match(/[a-zA-Z]/)[0];
      return char + uuid.substring(1);
    }

    const uuid = _uuidWithLetterStart();
    // Start button is in collapsible tr for new labs
    var [collapsibleTr, id] = _getTrAndId(this);
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
    // Need to create it here for JS context reasons
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
            .html(custom_utils.parseJSON(xhr.responseText)));
        $(`#${id}-log`).append(
          $("<div>").addClass("log-div").html(details)
        );
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
      const id = custom_utils.getId(this);
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
    var [collapsibleTr, id] = _getTrAndId(this);
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
    var name = options["name"];

    api.update_named_server(user, id, {
      data: JSON.stringify(options),
      success: function () {
        $(`#${id}-name-input`).val(options["name"]);
        // Reset all user inputs to the values saved in the global user options
        let available = checkIfAvailable(id, options);
        setUserOptions(id, options, available);
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

  function _getTrAndId(element) {
    let tr = $(element).parents("tr");
    let id = tr.data("server-id");
    return [tr, id];
  }

  function _disableTrButtons(tr) {
    // Disable buttons
    tr.find(".btn").addClass("disabled");
  }

  function _enableTrButtons(tr, running) {
    if (running) {
      // Show open/cancel for starting labs
      tr.find(".btn-na-lab, .btn-start-lab").addClass("d-none");
      tr.find(".btn-open-lab, .btn-cancel-lab").removeClass("d-none");
      // Disable until fitting event received from EventSource
      tr.find(".btn-open-lab, .btn-cancel-lab").addClass("disabled");
    }
    else {
      // Show start or na for non-running labs
      var na = tr.find(".na-status").text() || 0;
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
  }

  function _showErrorAlert(alert, name, text) {
    alert.children("span")
      .text(`Could not update ${name}. Error: ${text}`);
    alert
      .removeClass("alert-success p-0")
      .addClass("alert-danger show p-1");
  }


  function _updateTr(tr, id, options) {
    tr.find(".name-td").text(options.name);
    function _updateTd(key) {
      let configTdDiv = tr.find(`#${id}-config-td-div-${key}`);
      if (options[key]) configTdDiv.removeClass("d-none");
      else configTdDiv.addClass("d-none");
      let configDiv = tr.find(`#${id}-config-td-${key}`);
      configDiv.text(options[key]);
    }
    ["system", "flavor", "partition", "project",
      "runtime", "nodes", "gpus"].forEach(key => _updateTd(key));
  }

  function _createDataDict(collapsibleTr) {
    var options = {}
    options["name"] = _getDisplayName(collapsibleTr);

    function _addSelectValue(param) {
      var select = collapsibleTr.find(`select[id*=${param}]`);
      var value = select.val();
      if (param == "version") {
        param = "profile"
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

    ["version", "system", "flavor", "account",
      "project", "partition", "reservation"].forEach(key => _addSelectValue(key));
    ["nodes", "gpus", "runtime", "xserver"].forEach(key => _addInputValue(key));
    _addCbValues("userModules");
    return options;
  }
});
