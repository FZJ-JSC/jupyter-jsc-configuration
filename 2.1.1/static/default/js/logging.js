require(["jquery", "jhapi"], function (
  $,
  JHAPI,
) {
  "use strict";

  var base_url = window.jhdata.base_url;
  var api = new JHAPI(base_url);
  var systems = ["jhub", "unicoremgr", "k8smgrhdfcloud", "tunnel"];

  // Get LoggingHandler infos on page load
  $(document).ready(function () {
    systems.forEach(function (system) {
      var handlers = { "file": null, "stream": null, "smtp": null, "syslog": null }
      api.api_request(`logs/${system}/handler`, {
        success: function (data) {
          data.forEach(function (item) {
            var handler = item.handler;
            var config = item.configuration;
            for (const c in config) {
              var element = $(`#${system}-${handler}-${c}`);
              var value = config[c];
              if (typeof (value) == "object") {
                value = value.join(';');
              }
              element.val(value);
            }
            handlers[handler] = config;
          })

          // Can only create those handlers which do not exist
          for (const handler in handlers) {
            if (!handlers[handler]) {
              $(`#${system}-${handler}-patch, #${system}-${handler}-delete`).addClass("disabled");
              // Empty all settings
              $(`#${system}-${handler}-settings`).find("select, input").each(function () {
                $(this).val('');
              })
            } else {
              $(`#${system}-${handler}-create`).addClass("disabled");
            }
          }
        }  // success
      }) // api.api_request
    }) // systems.forEach
  });

  function updateHandler(system, handler) {
    api.api_request(`logs/${system}/handler/${handler}`, {
      success: function (data) {
        var config = data.configuration;
        for (const c in config) {
          var element = $(`#${system}-${handler}-${c}`);
          element.val(config[c]);
        }
      }
    })
  }

  function getConfig(system, handler) {
    var config = {};
    $(`#${system}-${handler}-settings`).find("select, input").each(function () {
      var value = $(this).val();
      var setting = $(this).attr("id").split('-')[2];
      if (value) {
        if ($(this).attr("type") == "number") value = parseInt(value);
        if ($(this).attr("id").includes("smtp-toaddr")) value = value.split(';');
        if ($(this).attr("id").includes("syslog-address")) {
          value = value.split(';');
          value[1] = parseInt(value[1]);
        }
        config[setting] = value;
      }
    })
    return config;
  }

  function create_handler(system, handler) {
    var output_area = $(`#${system}-${handler}-alert`);
    // Validate form
    var form = $(`#${system}-${handler}-form`);
    if (!form[0].checkValidity()) {
      form.addClass("was-validated");
      output_area.text("Incorrect input values.");
      return;
    }
    var data = {
      "handler": handler,
      "configuration": getConfig(system, handler)
    }
    api.api_request(`logs/${system}/handler`, {
      type: "POST",
      data: JSON.stringify(data),
      dataType: "text",
      success: function () {
        output_area.text(`Successfully created ${handler} handler.`);
        updateHandler(system, handler);
        $(`button[id^=${system}][id$=create]`).addClass("disabled");
        $(`button[id^=${system}][id$=patch]`).removeClass("disabled");
        $(`button[id^=${system}][id$=delete]`).removeClass("disabled");
      },
      error: function (xhr, textStatus, errorThrown) {
        output_area.text(`${xhr.status} ${errorThrown}`);
      }
    })
  }

  function patch_handler(system, handler) {
    var output_area = $(`#${system}-${handler}-alert`);
    // Validate form
    var form = $(`#${system}-${handler}-form`);
    if (!form[0].checkValidity()) {
      form.addClass("was-validated");
      output_area.text("Incorrect input values.");
      return;
    }
    var data = {
      "handler": handler,
      "configuration": getConfig(system, handler)
    }
    api.api_request(`logs/${system}/handler/` + handler, {
      type: "PATCH",
      data: JSON.stringify(data),
      dataType: "text",
      success: function () {
        output_area.text(`Successfully updated ${handler} handler.`);
        updateHandler(system, handler);
      },
      error: function (xhr, textStatus, errorThrown) {
        output_area.text(`${xhr.status} ${errorThrown}`);
      }
    })
  }

  function delete_handler(system, handler) {
    var output_area = $(`#${system}-${handler}-alert`);
    api.api_request(`logs/${system}/handler/` + handler, {
      type: "DELETE",
      dataType: "text",
      success: function () {
        output_area.text(`Successfully deleted ${handler} handler.`);
        $(`#${system}-${handler}-settings`).find("select, input").each(function () {
          $(this).val('');
        })
        $(`button[id^=${system}][id$=create]`).removeClass("disabled");
        $(`button[id^=${system}][id$=patch]`).addClass("disabled");
        $(`button[id^=${system}][id$=delete]`).addClass("disabled");
      },
      error: function (xhr, textStatus, errorThrown) {
        output_area.text(`${xhr.status} ${errorThrown}`);
      }
    })
  }

  systems.forEach(function (system) {
    $(`button[id^=${system}][id$=create]`).click(function () {
      var handler = $(this).attr("id").split('-')[1];
      create_handler(system, handler);
    });
    $(`button[id^=${system}][id$=patch]`).click(function () {
      var handler = $(this).attr("id").split('-')[1];
      patch_handler(system, handler);
    });
    $(`button[id^=${system}][id$=delete]`).click(function () {
      var handler = $(this).attr("id").split('-')[1];
      delete_handler(system, handler);
    });
  })
});