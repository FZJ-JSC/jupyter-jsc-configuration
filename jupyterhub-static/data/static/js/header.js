// $(function () {
//   // Multi Level dropdowns
//   $("ul.dropdown-menu [data-toggle='dropdown']").on("mouseenter", function (event) {
//     event.preventDefault();
//     event.stopPropagation();

//     if (!$(this).next().hasClass('show')) {
//       $(this).parents('.dropdown-menu').first().find('.show').removeClass("show");
//     }
//     $(this).siblings().toggleClass("show");

//     // Close submenues when parent menu closes
//     $(this).parents('li.nav-item.dropdown.show').on('hidden.bs.dropdown', function (e) {
//       $('.dropdown-submenu .show').removeClass("show");
//     });
//   });
// });