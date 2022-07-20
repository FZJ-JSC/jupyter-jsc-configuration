// $(document).ready(function () {
//   $('.left-tabs > li.nav-item').on('shown.bs.tab', function () {
//     var should_show = JSON.parse(localStorage.getItem("spawnTabs"));
//     if (!should_show) should_show = [];
//     var id = $(this).children().first().attr('id');
//     if (!(should_show.includes(id))) should_show.push(id);
//     localStorage.setItem("homeTabs", JSON.stringify(should_show));
//   });

//   $('.left-tabs > li.nav-item').on('hidden.bs.tab', function () {
//     var should_show = JSON.parse(localStorage.getItem("spawnTabs"));
//     if (!should_show) return;
//     var id = $(this).children().first().attr('id');
//     if (should_show.includes(id)) {
//       should_show.splice(should_show.indexOf(id), 1);
//     }
//     localStorage.setItem("homeTabs", JSON.stringify(should_show));
//   });

//   // Reopen open collapses on page reload
//   var tabs = JSON.parse(localStorage.getItem("spawnTabs"));
//   if (tabs) {
//     for (const item of tabs) {
//       var tabEl = $('#' + item);
//       if (tabEl.length) {
//         var tab = new bootstrap.Tab(tabEl);
//         tab.show();
//       }
//     }
//   }
// })

// Expand/collapse table rows
$('tr[data-server-name]').not('.progress-tr').not('.collapse-tr').on('click', function () {
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