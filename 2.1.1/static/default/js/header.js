$(window).on('load', function () {
  /* Set correct paddings and margins */
  spaceHeader();
    $(window).on('resize orientationchange', spaceHeader)
})

function spaceHeader() {
  var header = $("header");
  var nav = header.children().first();
  header.height(nav.height());
}