$(window).on('load', function () {
  /* Set correct paddings and margins */
  spaceContent();
  $(window).on('resize orientationchange', spaceContent)
})

$(document).ready(function () {
  /* Set active nav entry in sidebar */
  var pathname = window.location.pathname;
  $("#sidebar .nav-link").removeClass("active");
  if (pathname.includes("/hub/home") || pathname.includes("/hub/spawn-pending")) {
    setActive(/^JupyterLabs$/);
  }
  else if (pathname.includes("/hub/admin")) {
    setActive(/^Admin$/);
  }
  else if (pathname.includes("/hub/logging")) {
    setActive(/^Logging$/);
  }
})

function spaceContent() {
  var header = $("header");
  var first_nav = header.children().first();
  var second_nav = header.children().last();
  if (second_nav.css("display") != "none") {
    // Space header
    second_nav.css("margin-top", first_nav.height());
    // Space main
    $("main").removeClass("ms-sm-auto");
    // $("main").css("margin-top", header.height());
  }
  else {
    $("main").addClass("ms-sm-auto");
    // $("main").css("margin-top", first_nav.height());
  }
  $(".sidebar").css("padding-top", first_nav.height() + second_nav.height());
}

function setActive(regEx) {
  var navLink = $('#sidebar .nav-link').filter(function () {
    var text = $(this).text().trim();
    return regEx.test(text);
  });
  var navLinkDiv = navLink.parent();
  navLink.addClass("active");
  navLinkDiv.addClass("active");
  navLinkDiv.append('<div class="arrow-left ms-auto"></div>');
}

function removeActive(listItem) {
  var navLink = $(`#sidebar .nav-link:contains(${listItem})`);
  var navLinkDiv = navLink.parent();
  navLink.removeClass("active");
  navLinkDiv.removeClass("active");
  navLinkDiv.children().last().remove();
}