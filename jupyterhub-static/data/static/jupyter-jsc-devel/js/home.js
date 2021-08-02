// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi"], function (
  $,
  JHAPI,
) {
  "use strict";

  var base_url = window.jhdata.base_url;
  // var prefix = window.jhdata.prefix;
  var user = window.jhdata.user;
  // var user_active = window.jhdata.user_active;
  var api = new JHAPI(base_url);
  var cancel_url = window.jhdata.cancel_url;

  // Named servers buttons
  function getRow(element) {
    return element.parents("tr");
  }

  function disableRow(row) {
    row.find(".btn").addClass("disabled").off("click");
  }

  function enableRow(row, running) {
    // enable buttons on a server row
    // once the server is running or not
    row.find(".btn").removeClass("disabled");
    //row.find(".stop-server").click(stopServer);
    row.find(".stop-server").click(cancelServer);
    row.find(".delete-server").click(deleteServer);
    var na = row.find(".na_status").text();

    if (running) {
      row.find(".start-server").addClass("d-none");
      row.find(".delete-server").addClass("d-none");
      row.find(".stop-server").removeClass("d-none");
      row.find(".url-server").removeClass("d-none");
      row.find(".server-link").removeClass("d-none");
      row.find(".server-link-nourl").addClass("d-none");
    } else {
      var row_start = row.find(".start-server");
      row_start.removeClass("d-none");
      if (na == "1") {
        row_start.addClass("disabled");
        row_start.text("n/a");
      } else {
        row_start.removeClass("disabled");
        row_start.text("Start");
      }
      row.find(".delete-server").removeClass("d-none");
      row.find(".stop-server").addClass("d-none");
      row.find(".url-server").addClass("d-none");
      row.find(".server-link").addClass("d-none");
      row.find(".server-link-nourl").removeClass("d-none");
    }
  }

  function cancelServer() {
    var row = getRow($(this));
    var serverName = row.data("server-name");

    // before request
    disableRow(row);

    // request
    api.cancel_named_server(user, serverName, {
      success: function () {
        enableRow(row, false);
      },
    });
  }

  function stopServer() {
    var row = getRow($(this));
    var serverName = row.data("server-name");

    // before request
    disableRow(row);

    // request
    api.stop_named_server(user, serverName, {
      success: function () {
        enableRow(row, false);
      },
    });
  }

  function deleteServer() {
    var row = getRow($(this));
    var serverName = row.data("server-name");

    // before request
    disableRow(row);

    // request
    api.delete_named_server(user, serverName, {
      success: function () {
        row.remove();
      },
    });
  }

  // initial state: hook up click events
  $("#stop").click(function () {
    $("#start")
      .attr("disabled", true)
      .attr("title", "Your server is stopping")
      .click(function () {
        return false;
      });
    api.stop_server(user, {
      success: function () {
        $("#start")
          .text("Start My Server")
          .attr("title", "Start your default server")
          .attr("disabled", false)
          .off("click");
      },
    });
  });

  $(".new-server-btn-dashboard").click(function () {
    var row = getRow($(this));
    var serverName = row.find("#dashboardname").val().toLowerCase();
    var allowed = "abcdefghijklmnopqrstuvwxyz0123456789_";
    var b = true;
    var i = serverName.length;
    if (i > 30) {
      return;
    }
    if (i == 0) {
      var c = row.parent().children().length - 1;
      do {
        serverName = "dashboard_" + c;
        var start_server = document.getElementById("start-" + serverName);
        if (start_server != null) {
          c += 1;
        }
      } while (start_server != null);
    }
    while (i--) {
      if (!allowed.includes(serverName.charAt(i))) {
        b = false;
        break;
      }
    }
    if (b) {
      console.log("ABC");
      window.location.href = "../spawn/" + user + "/" + serverName + "?service=Dashboard";
    }
  });

  $(".new-server-btn").click(function () {
    var row = getRow($(this));
    //var serverName = row.find(".new-server-name").val().toLowerCase();
    var serverName = row.find("#labname").val().toLowerCase();
    var allowed = "abcdefghijklmnopqrstuvwxyz0123456789_";
    var b = true;
    var i = serverName.length;
    if (i > 30) {
      return;
    }
    if (i == 0) {
      var c = row.parent().children().length - 1;
      do {
        serverName = "jupyterlab_" + c;
        var start_server = document.getElementById("start-" + serverName);
        if (start_server != null) {
          c += 1;
        }
      } while (start_server != null);
    }
    while (i--) {
      if (!allowed.includes(serverName.charAt(i))) {
        b = false;
        break;
      }
    }
    if (b) {
      window.location.href = "../spawn/" + user + "/" + serverName;
    }
  });

  $("#cancel").click(function () {
    if (!$("#cancel").is("[disabled=disabled]")) {
      $("#cancel").attr("disabled", true);
      api.cancel_server(cancel_url);
    }
  });
  $("#cancel901").click(function () {
    if (!$("#cancel901").is("[disabled=disabled]")) {
      $("#cancel901").attr("disabled", true);
      api.cancel_server(cancel_url, { error: null });
      $("#loadinggif").hide();
      $("#h901").text("Server start cancelled by user.");
    }
  });

  function onClickVO() {
    var value = $(this).val();
    api.set_vo(value, {
      success: function () {
        $("#vo-select").val(value);
        location.reload();
      },
    });
  }

  $("#vo-select").change(onClickVO);
  $(".stop-server").click(cancelServer);
  $(".delete-server").click(deleteServer);
});
