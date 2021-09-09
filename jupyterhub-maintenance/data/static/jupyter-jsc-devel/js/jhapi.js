// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

define(["jquery", "utils"], function ($, utils) {
  "use strict";

  var JHAPI = function (base_url) {
    this.base_url = base_url;
  };

  var default_options = {
    type: "GET",
    contentType: "application/json",
    cache: false,
    dataType: "json",
    processData: false,
    success: null,
    tryCount: 5,
    error: function (xhr, textStatus, errorThrown) {
      if (xhr.status == 503) {
        this.tryCount--;
        if (this.tryCount >= 0) {
          $.ajax(this);
          return;
        }
        return;
      }
    },
  };

  var update = function (d1, d2) {
    $.map(d2, function (i, key) {
      d1[key] = d2[key];
    });
    return d1;
  };

  var ajax_defaults = function (options) {
    var d = {};
    update(d, default_options);
    update(d, options);
    return d;
  };

  JHAPI.prototype.api_request = function (path, options) {
    options = options || {};
    options = ajax_defaults(options || {});
    var url = utils.url_path_join(
      this.base_url,
      "api",
      utils.encode_uri_components(path)
    );
    $.ajax(url, options);
  };

  JHAPI.prototype.set_vo = function (value, options) {
    options = options || {};
    options = update(options, { type: "POST", dataType: null });
    this.api_request(utils.url_path_join("vo", value), options);
  };

  JHAPI.prototype.start_server = function (user, options) {
    options = options || {};
    options = update(options, { type: "POST", dataType: null });
    this.api_request(utils.url_path_join("users", user, "server"), options);
  };

  JHAPI.prototype.start_named_server = function (user, server_name, options) {
    options = options || {};
    options = update(options, { type: "POST", dataType: null });
    this.api_request(
      utils.url_path_join("users", user, "servers", server_name),
      options
    );
  };

  JHAPI.prototype.stop_server = function (user, options) {
    options = options || {};
    options = update(options, { type: "DELETE", dataType: null });
    this.api_request(utils.url_path_join("users", user, "server"), options);
  };

  JHAPI.prototype.cancel_named_server = function (user, server_name, options) {
    options = options || {};
    options = update(options, { type: "POST" });
    options.data = JSON.stringify({ error: "cancelclick" });
    this.api_request(
      utils.url_path_join("users", user, "servers", server_name, "cancel"),
      options
    );
  };

  JHAPI.prototype.cancel_server = function (cancel_url, options) {
    options = options || {};
    options = update(options, { type: "POST" });
    options.data = JSON.stringify({ error: "cancelclick" });
    this.api_request(cancel_url, options);
  };

  JHAPI.prototype.stop_named_server = function (user, server_name, options) {
    options = options || {};
    options = update(options, { type: "DELETE", dataType: null });
    this.api_request(
      utils.url_path_join("users", user, "servers", server_name),
      options
    );
  };

  JHAPI.prototype.delete_named_server = function (user, server_name, options) {
    options = options || {};
    options.data = JSON.stringify({ remove: true });
    return this.stop_named_server(user, server_name, options);
  };

  JHAPI.prototype.list_users = function (options) {
    this.api_request("users", options);
  };

  JHAPI.prototype.get_user = function (user, options) {
    this.api_request(utils.url_path_join("users", user), options);
  };

  JHAPI.prototype.add_users = function (usernames, userinfo, options) {
    options = options || {};
    var data = update(userinfo, { usernames: usernames });
    options = update(options, {
      type: "POST",
      dataType: null,
      data: JSON.stringify(data),
    });

    this.api_request("users", options);
  };

  JHAPI.prototype.edit_user = function (user, userinfo, options) {
    options = options || {};
    options = update(options, {
      type: "PATCH",
      dataType: null,
      data: JSON.stringify(userinfo),
    });

    this.api_request(utils.url_path_join("users", user), options);
  };

  JHAPI.prototype.admin_access = function (user, options) {
    options = options || {};
    options = update(options, {
      type: "POST",
      dataType: null,
    });

    this.api_request(
      utils.url_path_join("users", user, "admin-access"),
      options
    );
  };

  JHAPI.prototype.delete_user = function (user, options) {
    options = options || {};
    options = update(options, { type: "DELETE", dataType: null });
    this.api_request(utils.url_path_join("users", user), options);
  };

  JHAPI.prototype.request_token = function (user, props, options) {
    options = options || {};
    options = update(options, { type: "POST" });
    if (props) {
      options.data = JSON.stringify(props);
    }
    this.api_request(utils.url_path_join("users", user, "tokens"), options);
  };

  JHAPI.prototype.revoke_token = function (user, token_id, options) {
    options = options || {};
    options = update(options, { type: "DELETE" });
    this.api_request(
      utils.url_path_join("users", user, "tokens", token_id),
      options
    );
  };

  JHAPI.prototype.remove_2fa = function (user, options) {
    options = options || {};
    options = update(options, { type: "DELETE", dataType: null });
    this.api_request(utils.url_path_join("2FA"), options);
  };

  JHAPI.prototype.activate_2fa = function (user, options) {
    options = options || {};
    options = update(options, { type: "POST", dataType: null });
    this.api_request(utils.url_path_join("2FA"), options);
  };

  JHAPI.prototype.shutdown_hub = function (data, options) {
    options = options || {};
    options = update(options, { type: "POST" });
    if (data) {
      options.data = JSON.stringify(data);
    }
    this.api_request("shutdown", options);
  };

  return JHAPI;
});
