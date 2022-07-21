$(document).ready(function () {
  var tr = $('tr[data-server-name]').not('.progress-tr').not('.collapse-tr');
  var collapse = tr.next().find(".collapse");
  var first_td = tr.children().first();
  var icon = first_td.children().first();
  var name = tr.data("server-name");
  // Open collapse
  icon.removeClass('collapsed');
  new bootstrap.Collapse(collapse);
  // and change to log vertical tag
  var trigger = $("#" + name + "-logs-tab");
  var tab = new bootstrap.Tab(trigger);
  tab.show();
})

// Expand/collapse table rows
$('tr[data-server-name]').not('.progress-tr').not('.collapse-tr').click(function () {
  var collapse = $(this).next().find('.collapse');
  var first_td = $(this).children().first();
  var icon = first_td.children().first();
  var hidden = collapse.css('display') == 'none' ? true : false;

  if (hidden) {
    icon.removeClass('collapsed');
    new bootstrap.Collapse(collapse);
  } else {
    icon.addClass('collapsed');
    new bootstrap.Collapse(collapse);
  }
});

// Change to log vertical tag on toggle logs
$(".progress-log-btn, .progress-info-text").click(function (event) {
  var tr = $(this).parents("tr");
  var collapse = tr.next().find(".collapse");
  var hidden = collapse.css("display") == "none" ? true : false;
  var name = tr.data("server-name");

  console.log(hidden, $("#" + name + "-logs-tab").hasClass("active"));

  // Do not hide collapse if already open, but not showing the logs tab
  if (!hidden && !$("#" + name + "-logs-tab").hasClass("active")) {
    event.preventDefault();
    event.stopPropagation();
  }
  else if (!hidden) {
    return; // do not change to log tab if we should close the collapse 
  }
  // Change to log vertical tab
  var trigger = $("#" + name + "-logs-tab");
  var tab = new bootstrap.Tab(trigger);
  tab.show();
});