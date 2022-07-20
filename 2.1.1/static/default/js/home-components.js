// // Reopen selected tabs
// $(document).ready(function () {
//   $('.left-tabs > li.nav-item').on('shown.bs.tab', function () {
//     var should_show = JSON.parse(localStorage.getItem("homeTabs"));
//     if (!should_show) should_show = [];
//     var id = $(this).children().first().attr('id');
//     if (!(should_show.includes(id))) should_show.push(id);
//     localStorage.setItem("homeTabs", JSON.stringify(should_show));
//   });

//   $('.left-tabs > li.nav-item').on('hidden.bs.tab', function () {
//     var should_show = JSON.parse(localStorage.getItem("homeTabs"));
//     if (!should_show) return;
//     var id = $(this).children().first().attr('id');
//     if (should_show.includes(id)) {
//       should_show.splice(should_show.indexOf(id), 1);
//     }
//     localStorage.setItem("homeTabs", JSON.stringify(should_show));
//   });

//   // Reopen open collapses on page reload
//   var tabs = JSON.parse(localStorage.getItem("homeTabs"));
//   if (tabs) {
//     for (const item of tabs) {
//       var tabEl = $('#' + item);
//       if (tabEl.length) {
//         var tab = new bootstrap.Tab(tabEl);
//         tab.show();
//       }
//     }
//   }
//   // console.log(JSON.parse(localStorage.getItem("homeTabs")))
// })

// Check if warning badge whould be shown in tab
$("[id*=tab-warning]").on("change", function () {
  var tab_warning = $(this);
  var tab = tab_warning.parent();
  var tab_content = $(tab.data("bsTarget"));
  var badges = tab_content.find(".badge");
  var should_show = false;

  badges.each(function () {
    if ($(this).css("display") != "none") should_show = true;
  })

  if (should_show && !tab.hasClass("disabled")) {
    tab_warning.show();
  } else {
    tab_warning.hide();
  }
});

// Remove warning icons when clicking on inputs
function onFocus(select, tab_name, setting = "select") {
  var id = get_id(select);
  var warning_id = select.attr("id").replace("-" + setting, "-warning");
  select.removeClass("border-warning");
  $("#" + warning_id).hide();
  $("#" + id + "-" + tab_name + "-tab-warning")[0].dispatchEvent(new Event("change"));
}

$("div[id*=service] input").on("input", function () {
  onFocus($(this), "service", setting = "input");
});

$("div[id*=service] select").focus(function () {
  onFocus($(this), "service");
});

$("div[id*=options] select").focus(function () {
  onFocus($(this), "options");
});

$("div[id*=resources] input").focus(function () {
  onFocus($(this), "resources", setting = "input");
});

$("div[id*=reservation] select").focus(function () {
  onFocus($(this), "reservation");
});

// Check on click if we can remove the warning badge in tab
$("[id$=tab").on("click", function () {
  var tab = $(this);
  var tab_content = $(tab.data("bsTarget"));
  var badges = tab_content.find(".badge");

  badges.each(function () {
    var parent_div = $(this).parents("div").first();
    // There might be a warning because an existing value does not exist anymore
    // In that case, the warning badge will be displayed, but not the parent div
    if ($(this).css("display") != "none" && parent_div.css("display") == "none") {
      $(this).hide(); // We manually hide the warning badge once the tab has been clicked
    }
  })
  // Send change event to the tab warning to see if we should still show the warning in the tab
  var tab_warning = tab.find("[id*=warning");
  tab_warning[0].dispatchEvent(new Event("change"));
});

// Remove all warning badges for a lab
function removeWarnings(name) {
  $("#" + name + "-configuration input, #" + name + "-configuration select").each(function() {
    $(this)[0].dispatchEvent(new Event("focus"));
  });
}

// Toggle the collapse on table row click
$("tr[data-server-name]").not(".progress-tr").not(".collapse-tr").on("click", function () {
  var collapse = $(this).next().find(".collapse");
  var first_td = $(this).children().first();
  var icon = first_td.children().first();
  var hidden = collapse.css("display") == "none" ? true : false;

  if (hidden) {
    icon.removeClass("collapsed");
    new bootstrap.Collapse(collapse);
  } else {
    icon.addClass("collapsed");
    new bootstrap.Collapse(collapse);
  }
});
// But not on click of the action td
$(".actions-td").on("click", function (event) {
  event.preventDefault();
  event.stopPropagation();
})

// Change to log vertical tag on toggle logs
// $(".btn[id*=progress-log-btn]").on("click", function(event) {
$(".progress-log-btn").on("click", function (event) {
  var tr = $(this).parents("tr");
  var collapse = tr.next().find(".collapse");
  var hidden = collapse.css("display") == "none" ? true : false;
  var name = tr.data("server-name");
  // Do not hide collapse if already open, but not showing the logs tab
  if (!hidden && !$("#" + name + "-logs-tab").hasClass("show")) {
    event.preventDefault();
    event.stopPropagation();
  }
  // Change to log vertical tag
  var trigger = $("#" + name + "-logs-tab");
  var tab = new bootstrap.Tab(trigger);
  tab.show();
});

// Update styling of select components depending on available values
function updateSelect(select, id, value, old_value, values, tab_id="options") {
  // For some systems (e.g. cloud), some options are not available
  var na = false;
  if ( select.html() == "" ) {
    select.append("<option disabled>Not available</option>");
    select.addClass("text-muted");
    select.removeAttr("required");
    na = true;
  }

  // Disable select when there is only one option
  // Instead make div clickable to remove warning on select
  if ( values.length == 1 || na ) {
    select.addClass("disabled");
    select.parent().click(function() {
      var warning_id = select.attr("id").replace("-select", "-warning");
      var warning = $("#" + warning_id);
      var tab_warning = $("#" + id + "-" + tab_id + "-tab-warning");

      select.removeClass("border-warning");
      warning.hide();
      tab_warning[0].dispatchEvent(new Event("change"));
    })
  } else {
    select.removeClass("disabled");
    select.parent().off("click");
  }

  // Value is only supplied when setting values from saved values when first loading or resetting
  if ( !value ) {
    updateSelectValue(id, old_value, values, select, tab_id);
  } else {
    if (value == "None") select.prop("selectedIndex", 0);
    else select.val(value);
  }
}

function updateSelectValue(id, old_value, values, select, tab_id="options") {
  var warning_id = select.attr("id").replace("-select", "-warning");
  var warning = $("#" + warning_id);
  var tab_warning = $("#" + id + "-" + tab_id + "-tab-warning");

  // No changes if option is not available (value.lenth == 0)
  if (old_value == null && values.length == 0) {
    select.prop("selectedIndex", 0);
    select[0].dispatchEvent(new Event("change"));
    return;
  }

  if ( values.includes(old_value) ) {
    select.val(old_value);
  } else {
    select.prop("selectedIndex", 0);
    select.addClass("border-warning");
    warning.show();
  }
  select[0].dispatchEvent(new Event("change"));
  tab_warning[0].dispatchEvent(new Event("change"));
}

// Update styling of input components depending on available values
function updateInput(id, old_value, value, min, max, input, tab_id="resources") {
  var warning_id = input.attr("id").replace("-input", "-warning");
  var warning = $("#" + warning_id);
  var tab_warning = $("#" + id + "-" + tab_id + "-tab-warning");
  var tab_link = tab_warning.parent();

  if ( old_value != "" ) {
    if ( old_value >= min && old_value <= max) {
      input.val(old_value);
    } else {
      input.val(value);
      input.addClass("border-warning");
      warning.show();
    }
    // Moved change event to end of updateResources function
    // so that the warning symbol will disappear if the tab gets disabled
    // tab_warning[0].dispatchEvent(new Event("change"));
  }
  else if ( old_value == "" && tab_link.hasClass("disabled") ) {
    input.val(value);
    input.addClass("border-warning");
    warning.show();
    // tab_warning[0].dispatchEvent(new Event("change"));
  }
}