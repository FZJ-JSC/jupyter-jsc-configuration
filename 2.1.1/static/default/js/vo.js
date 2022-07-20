require(["jquery", "jhapi"], function (
  $,
  JHAPI,
) {
  "use strict";

  var base_url = window.jhdata.base_url;
  var api = new JHAPI(base_url);

  $(document).ready(function () {
    var value = $("#vo-active").text()
    $("[name=vo-radio]").val([value]);
    // $("#vo-select").val($("#vo-active").text());
  });

  function onClickVO() {
    var value = $(this).val();
    api.set_vo(value, {
      success: function () {
        $("#vo-select").val(value);
        if ( location.pathname.includes("home") || location.pathname.includes("groups")) location.reload();
      },
    });
  }

  $("[name=vo-radio]").change(onClickVO);
});