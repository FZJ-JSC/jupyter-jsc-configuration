$(document).ready(function () {
  $('.collapse').not('.sidebar').on('shown.bs.collapse', function () {
    var should_show = JSON.parse(localStorage.getItem("collapses"));
    if (!should_show) should_show = [];
    var id = $(this).attr('id');
    if (!(should_show.includes(id))) should_show.push(id);
    localStorage.setItem("collapses", JSON.stringify(should_show));
  })

  $('.collapse').not('.sidebar').on('hidden.bs.collapse', function () {
    var should_show = JSON.parse(localStorage.getItem("collapses"));
    if (!should_show) return;
    var id = $(this).attr('id');
    if (should_show.includes(id)) {
      should_show.splice(should_show.indexOf(id), 1);
    }
    localStorage.setItem("collapses", JSON.stringify(should_show));
  })

  // Reopen open collapses on page reload
  var collapses = JSON.parse(localStorage.getItem("collapses"));
  if (collapses) {
    for (const item of collapses) {
      var collapse = $('#' + item);
      if (collapse.length) {
        new bootstrap.Collapse('#' + item);
        var parent = $("#" + item).parent();
        if (parent.prop('tagName') == "TD") {
          // Manually change icon for table collpases
          var details_td = $('[data-bs-target="#' + item + '"]');
          var icon = details_td.find('.accordion-icon');
          icon.removeClass("collapsed");
        }
      }
    }
  }

  // console.log(JSON.parse(localStorage.getItem("collapses")))

});