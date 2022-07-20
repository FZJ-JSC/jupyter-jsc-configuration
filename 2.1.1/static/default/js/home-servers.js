// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi", "utils"], function (
  $,
  JHAPI,
  utils
) {
  "use strict";

  var base_url = window.jhdata.base_url;
  var user = window.jhdata.user;
  var api = new JHAPI(base_url);


  /*
  Listen for new pending spawner and stopped server notifications
  */
  var update_start_url = utils.url_path_join(jhdata.base_url, "api/users", user, "notifications", "spawners", "spawn");
  var startEvtSource = new EventSource(update_start_url);
  startEvtSource.onmessage = function (e) {
    var data = JSON.parse(e.data)
    for (const name in data) {
      if (!(name in spawn_events)) {
        location.reload();
        return;
      }

      if (!(name in evtSources)) {
        var progress_url = utils.url_path_join(jhdata.base_url, "api/users", user, "servers", name, "progress");
        var progress_bar = $("#" + name + "-progress-bar");
        var progress_log = $("#" + name + "-progress-log");
        var log_select = $("#" + name + "-log-select");

        // Save latest logs and update log select
        update_spawn_events_dict(name, log_select);

        evtSources[name] = new EventSource(progress_url);
        evtSources[name]["name"] = name;
        evtSources[name]["progress_bar"] = progress_bar;
        evtSources[name]["progress_log"] = progress_log;
        evtSources[name].onmessage = function (e) {
          onEvtMessage(e, evtSources[name], evtSources[name]["progress_bar"], evtSources[name]["progress_log"]);
        }

        progress_bar.removeClass("bg-success bg-danger");
        progress_bar.css("width", "0%");
        progress_log.html("");

        // Update buttons to reflect pending state
        var row = $('tr[data-server-name="' + name + '"]').first();
        enableRow(row, true);
      }
    }
  }

  var update_stop_url = utils.url_path_join(jhdata.base_url, "api/users", user, "notifications", "spawners", "stop");
  var stopEvtSource = new EventSource(update_stop_url);
  stopEvtSource.onmessage = function (e) {
    var data = JSON.parse(e.data);
    for (const name in data) {
      const html_message = data[name].html_message;
      var progress_bar = $("#" + name + "-progress-bar");
      var progress_log = $("#" + name + "-progress-log");
      var row = $('tr[data-server-name="' + name + '"]').first();
      // Only log message if it hasn't been logged yet      
      no_duplicate_log(html_message, progress_log);
      progress_bar.removeClass("bg-success");
      progress_bar.width(0);
      enableRow(row, false);
    }
  }


  /*
  Callbacks to handle button clicks
  */

  function getRow(button) {
    return button.parents("tr");
  }

  function getCollapse(row) {
    var server_name = row.data("server-name");
    var collapse = row.siblings(`.collapse-tr[data-server-name=${server_name}]`);
    return collapse;
  }

  function disableRow(tr) {
    // Disable buttons
    tr.find("button").addClass("disabled");
  }

  function enableRow(tr, running) {
    var na = tr.find(".na-status").text()
    tr.find("button").removeClass("disabled");

    if (running) {
      tr.find(".na").addClass("d-none")
      tr.find(".start").addClass("d-none");
      tr.find(".open").removeClass("d-none");
      tr.find(".cancel").removeClass("d-none");
      // Disable until fitting event received from EventSource
      tr.find(".open").addClass("disabled");
      tr.find(".cancel").addClass("disabled");
    } else {
      if (na == "1") {
        tr.find(".na").removeClass("d-none")
        tr.find(".start").addClass("d-none");
      } else {
        tr.find(".na").addClass("d-none")
        tr.find(".start").removeClass("d-none");
      }
      tr.find(".open").addClass("d-none");
      tr.find(".cancel").addClass("d-none");
      tr.find(".stop").addClass("d-none");
    }
  }

  function cancelServer(event) {
    event.preventDefault();
    event.stopPropagation();

    var tr = getRow($(this));
    var server_name = tr.data("server-name");
    disableRow(tr);

    api.cancel_named_server(user, server_name, {
      success: function () {
        enableRow(tr, false);
        // Only reset progress bar if stopping a running server
        // If cancelling, we want to keep the progress indicator
        var progress_bar = tr.find(".progress-bar");
        if (progress_bar.hasClass("bg-success")) {
          progress_bar.removeClass("bg-sucess");
          progress_bar.width(0);
          progress_bar.html('');
        }
      },
    });
  }

  function stopServer(event) {
    event.preventDefault();
    event.stopPropagation();

    var tr = getRow($(this));
    var server_name = tr.data("server-name");
    disableRow(tr);

    api.stop_named_server(user, server_name, {
      success: function () {
        enableRow(tr, false);
        // Only reset progress bar if stopping a running server
        // If cancelling, we want to keep the progress indicator
        var progress_bar = tr.find(".progress-bar");
        if (progress_bar.hasClass("bg-success")) {
          progress_bar.removeClass("bg-sucess");
          progress_bar.width(0);
          progress_bar.html('');
        }
      },
    });
  }

  function deleteServer(event) {
    event.preventDefault();
    event.stopPropagation();

    var collapse_row = getRow($(this));
    disableRow(collapse_row);

    var server_name = collapse_row.data("server-name");
    var tr = collapse_row.siblings(`[data-server-name=${server_name}]`);

    api.delete_named_server(user, server_name, {
      success: function () {
        tr.each(function () {
          $(this).remove();
        })
        collapse_row.remove();
      },
    });
  }

  function startServer(event) {
    event.preventDefault();
    event.stopPropagation();

    // askForNotificationPermission();

    var tr = getRow($(this));
    var collapse = getCollapse(tr);
    disableRow(tr);

    var name = tr.data("server-name");
    var display_name = tr.find("th").text();
    var url = utils.url_path_join(base_url, "spawn", user, name);
    url = createUrlAndUpdateTr(url, collapse, tr);
    $(this).attr("href", url);

    var options = createDataDict(collapse, display_name);
    updateTr(collapse, tr);

    // Validate the form and start spawn only after validation
    try {
      $(`form[id*=${name}]`).submit();
      var progress_bar = $("#" + name + "-progress-bar");
      // Get the card instead of the parent div for the log
      var progress_log = $("#" + name + "-progress-log");
      var log_select = $("#" + name + "-log-select");
      progress_bar.removeClass("bg-success bg-danger");
      progress_bar.css("width", "0%");
      progress_log.html("");
      var newTab = window.open("about:blank");

      api.start_named_server(user, name, {
        data: JSON.stringify(options),
        success: function () {
          // Save latest log to time stamp and empty it
          update_spawn_events_dict(name, log_select);

          newTab.location.href = url;
          // hook up event-stream for progress
          var progress_url = utils.url_path_join(jhdata.base_url, "api/users", jhdata.user, "servers", name, "progress");
          if (!(name in evtSources)) {
            evtSources[name] = new EventSource(progress_url);
            evtSources[name]["name"] = name;
            evtSources[name]["progress_bar"] = progress_bar;
            evtSources[name]["progress_log"] = progress_log;
            evtSources[name].onmessage = function (e) {
              onEvtMessage(e, evtSources[name], evtSources[name]["progress_bar"], evtSources[name]["progress_log"]);
            }
          }

        },
        error: function (xhr, textStatus, errorThrown) {
          newTab.close();
          progress_bar.css("width", "100%");
          progress_bar.attr("aria-valuenow", 100);
          progress_bar.addClass("bg-danger");
          progress_log.append($("<div>").html(
            `Could not request spawn. Error: ${xhr.status} ${errorThrown}`)
          )
          enableRow(tr, false);
        }
      });
      enableRow(tr, true);
    } catch (e) {
      enableRow(tr, false);
    }
  }

  function startNewServer() {
    function uuidv4() {
      return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
      );
    }

    function uuidv4hex() {
      return ([1e7, 1e3, 4e3, 8e3, 1e11].join('')).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
    }

    function uuid_with_letter_start() {
      let uuid = uuidv4hex();
      let char = Math.random().toString(36).match(/[a-zA-Z]/)[0];
      return char + uuid.substring(1);
    }

    var server_name = uuid_with_letter_start();
    var display_name = $("#new_jupyterlab-name-input").val();
    // Automatically set name if none was specified
    if (display_name == "") {
      var c = 1;
      $("th[scope=row]").each(function () {
        var name = $(this).html();
        if (RegExp(/^jupyterlab_[0-9]*[0-9]$/).test(name)) c += 1;
      })
      display_name = "jupyterlab_" + c;
      $("#new_jupyterlab-name-input").val(display_name); // Set name for user
    }

    $(this).attr("disabled", true);
    var button = $(this);
    var spinner = $(this).children().first();
    var alert = $(this).siblings(".alert");
    spinner.removeClass("d-none");

    var url = utils.url_path_join(base_url, "spawn", user, server_name);
    url = createUrlAndUpdateTr(url, $("#new_jupyterlab-configuration"), display_name);
    $(this).attr("href", url);

    var parent = $("#new_jupyterlab-dialog").find(".modal-content");
    var options = createDataDict(parent, display_name);

    try {
      $("form[id*=new_jupyterlab]").submit();
      var newTab = window.open("about:blank");
      alert.children("span").text(`Waiting for ${display_name} to start...`);
      alert.removeClass("alert-danger").addClass("show alert-dark");
      api.start_named_server(user, server_name, {
        data: JSON.stringify(options),
        success: function () {
          newTab.location.href = url;
          var myModal = $("#new_jupyterlab-dialog");
          var modal = bootstrap.Modal.getInstance(myModal);
          modal.hide();
          button.removeAttr("disabled");
          spinner.addClass("d-none");
          alert.removeClass("show");
          location.reload();
        },
        error: function (xhr, textStatus, errorThrown) {
          newTab.close();
          spinner.addClass("d-none");
          button.removeAttr("disabled");
          alert.removeClass("alert-dark").addClass("show alert-danger");
          alert.children("span").text(`Could not start ${display_name}. Error: ${xhr.status} ${errorThrown}`);
        }
      });
    } catch (e) {
      $(this).removeAttr("disabled");
    }
  }

  function openServer(event) {
    event.preventDefault();
    event.stopPropagation();

    var url = $(this).data("server-url");
    window.open(url, "_blank");
  }

  $(".cancel").click(cancelServer);
  $(".stop").click(stopServer);
  $(".delete").click(deleteServer);
  $(".start").click(startServer);
  $("#new_jupyterlab-start-btn").click(startNewServer);
  $(".open").click(openServer);


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
      // Open the collapse if it was hidden
      var collapse = $(this).parents(".collapse");
      var first_td = $(this).parents("tr").prev().children().first();
      var icon = first_td.children().first();
      var hidden = collapse.css("display") == "none" ? true : false;
      if (hidden) {
        icon.removeClass("collapsed");
        new bootstrap.Collapse(collapse);
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
    var collapse = $(this).parents(".collapse");
    var tr = $(this).parents("tr").prev();
    var alert = $(this).siblings(".alert");

    var server_name = get_id($(this));
    var display_name = collapse.find("input[id*=name]").val();
    var options = createDataDict(collapse, display_name);

    api.update_named_server(user, server_name, {
      data: JSON.stringify(options),
      success: function () {
        // Update table data entries
        updateTr(collapse, tr);
        // Update user options
        user_options[server_name] = options;
        // Update alert message
        alert.children("span").text(`Successfully updated ${display_name}.`);
        alert.removeClass("alert-danger pe-none");
        alert.addClass("alert-success show");
        // Disable edit buttons again
        $("#" + server_name + "-save-btn").attr("disabled", true);
        $("#" + server_name + "-reset-btn").attr("disabled", true);
      },
      error: function (xhr, textStatus, errorThrown) {
        alert.children("span").text(`Could not update ${display_name}. Error: ${xhr.status} ${errorThrown}`);
        alert.removeClass("alert-success pe-none");
        alert.addClass("alert-danger show");
      }
    });
  }

  function revertChanges() {
    var collapse = $(this).parents(".collapse");
    var tr = $(this).parents("tr").prev();
    var alert = $(this).siblings(".alert");

    var server_name = get_id($(this));
    var display_name = collapse.find("input[id*=name]").val();
    var options = user_options[server_name];

    api.update_named_server(user, server_name, {
      data: JSON.stringify(options),
      success: function () {
        // setValues and removeWarning from new_home.html
        setValues(server_name, user_options[server_name]);
        removeWarnings(server_name); // Remove all warning badges
        // Update table data entries
        updateTr(collapse, tr)
        // Show first tab after resetting values
        var trigger = $("#" + server_name + "-service-tab");
        var tab = new bootstrap.Tab(trigger);
        tab.show();
        // Update alert message
        alert.children("span").text(`Successfully reverted settings back for ${display_name}.`);
        alert.removeClass("alert-danger pe-none");
        alert.addClass("alert-success show");
        // Disable edit buttons again
        $("#" + server_name + "-save-btn").attr("disabled", true);
        $("#" + nserver_nameame + "-reset-btn").attr("disabled", true);
      },
      error: function (xhr, textStatus, errorThrown) {
        alert.children("span").text(`Could not update ${display_name}. Error: ${xhr.status} ${errorThrown}`);
        alert.removeClass("alert-success pe-none");
        alert.addClass("alert-danger show");
      }
    });
  }

  $(".save").click(saveChanges);
  $(".reset").click(revertChanges);

  // Check if there are changes and thus if the save and revert buttons should be enabled
  $("select, input").not($("select[id*=log]")).change(function () {
    var that = $(this);
    var id = get_id(that);
    var option = $(this).attr("id").split('-')[1];
    var options = user_options[id];

    if (options) {
      switch (option) {
        case "type":
          var option_key = "options_input";
          break;
        case "nodes":
        case "runtime":
          var option_key = "resource_" + option[0].toUpperCase() + option.substring(1);
          break;
        case "gpus":
          var option_key = "resource_GPUS";
          break;
        default:
          var option_key = option + "_input";
      }

      var old_value = options[option_key];
      if (that.val() != old_value) {
        $("#" + id + "-save-btn").removeAttr("disabled");
        $("#" + id + "-reset-btn").removeAttr("disabled");
      }
    }
  })


  /*
  Util functions
  */
  function createUrlAndUpdateTr(url, parent, display_name, tr) {
    url += "?vo=" + $("#vo-form input[type='radio']:checked").val();
    url += "&name=" + display_name;

    function addParameter(param, input = false) {
      if (input) { // <input>
        var input = parent.find(`input[id*=${param}]`);
        var parent_div = input.parents(".row").first();
        if (parent_div.css("display") == "none") {
          return;
        }
        var value = input.val();
        if (param == "runtime") {
          value = value * 60;
        }
      }
      else { // <select>
        var select = parent.find(`select[id*=${param}]`);
        var value = select.val();

        if (param == "type") {
          param = "service";
          value = "JupyterLab/" + value;
        }

        // For new jupterlabs, no tr exists that can be updated
        if (tr) {
          switch (param) {
            case "system":
              var td = tr.find(".system-td");
              td.text(value);
              break;
            case "partition":
              var td = tr.find(".partition-td");
              td.text(value);
              break;
            case "project":
              var td = tr.find(".project-td");
              td.text(value);
              break;
          }
        }
      }

      if (value != null && value != "") url += "&" + param + "=" + value;
    }

    addParameter("type");  // service
    addParameter("system");
    addParameter("account");
    addParameter("project");
    addParameter("partition");
    addParameter("reservation");
    addParameter("nodes", true);
    addParameter("gpus", true);
    addParameter("runtime", true);
    return url;
  }

  function createDataDict(parent, display_name) {
    var user_options = {}
    user_options["vo"] = $("#vo-form input[type='radio']:checked").val();
    user_options["name"] = display_name;

    function addParameter(param, input = false) {
      if (input) { // <input>
        var input = parent.find(`input[id*=${param}]`);
        var parent_div = input.parents(".row").first();
        if (parent_div.css("display") == "none") {
          return;
        }
        var value = input.val();
        if (param == "runtime") {
          value = value * 60;
        }
      }
      else { // <select>
        var select = parent.find(`select[id*=${param}]`);
        var value = select.val();
        if (param == "type") {
          value = "JupyterLab/" + value;
          user_options["service"] = value;
          return;
        }
      }

      if (value != null) user_options[param] = value;
    }

    addParameter("type"); // service
    addParameter("system");
    addParameter("account");
    addParameter("project");
    addParameter("partition");
    addParameter("reservation");
    addParameter("nodes", true);
    addParameter("gpus", true);
    addParameter("runtime", true);
    return user_options;
  }

  function updateTr(collapse, tr) {
    var system_td = tr.find(".system-td");
    system_td.text(collapse.find("select[id*=system]").val());
    var partition_td = tr.find(".partition-td");
    partition_td.text(collapse.find("select[id*=partition]").val());
    var project_td = tr.find(".project-td");
    project_td.text(collapse.find("select[id*=project]").val());
  }

  function update_spawn_events_dict(name, log_select) {
    // Save latest log to time stamp and empty it
    const start_event = spawn_events[name]["latest"][0];
    const start_message = start_event.html_message;
    var re = /([0-9]+(_[0-9]+)+).*[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,3})?/;
    var start_time = re.exec(start_message)[0];
    spawn_events[name][start_time] = spawn_events[name]["latest"];
    spawn_events[name]["latest"] = [];
    log_select.append(`<option value="${start_time}">${start_time}</option>`);
  }

  /* Moved to home.html */
  // Handle EventSource message
  // function onEvtMessage(event, evtSource, progress_bar, progress_log) {
  // }
});
