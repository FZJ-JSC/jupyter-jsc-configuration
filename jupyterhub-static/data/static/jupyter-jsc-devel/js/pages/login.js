// $("#btn-login").click(function () {
//     var url = window.location.search;
//     if (!$("#login").is("[disabled=disabled]")) {
//         window.location.href = "/hub/oauth_login" + url;
//     }
// });

// function ready() {
//     Math.floor(Math.random() * 4) + 1;
// }

// function _ready(n) {
//   $(".resize-text-button").textfit("bestfit_button_start");
//   $(".resize-text").textfit("bestfit_button_start_after");
//   $("#text-three").textfit("bestfit");
//   var fs = $("#text-three").css("font-size");
//   //$("#text-zero").css("font-size", fs);
//   $("#text-one").css("font-size", fs);
//   $("#text-two").css("font-size", fs);
//   $("#text-four").css("font-size", fs);
//   $("#header-four").textfit("bestfit");
//   var fs = $("#header-four").css("font-size");
//   //$("#header-zero").css("font-size", fs);
//   $("#header-one").css("font-size", fs);
//   $("#header-two").css("font-size", fs);
//   $("#header-three").css("font-size", fs);
//   totalDivs(n);
// }

// function resize() {
    //   $(".resize-text-button").textfit("bestfit_button_start");
    // $(".resize-text").textfit("bestfit_button_start_after");
    //   $("#text-three").textfit("bestfit");
    //   var fs = $("#text-three").css("font-size");
    //   //$("#text-zero").css("font-size", fs);
    //   $("#text-one").css("font-size", fs);
    //   $("#text-two").css("font-size", fs);
    //   $("#text-four").css("font-size", fs);
    //   $("#header-four").textfit("bestfit");
    //   var fs = $("#header-four").css("font-size");
    //   //$("#header-zero").css("font-size", fs);
    //   $("#header-one").css("font-size", fs);
    //   $("#header-two").css("font-size", fs);
    //   $("#header-three").css("font-size", fs);
// }

// function totalDivs(n) {
//   slideIndex = n;
//   showDivs(n);
// }

// function plusDivs(n) {
//   showDivs((slideIndex += n));
// }

// function showDivs(n) {
//   var i;
//   var x = document.getElementsByClassName("content-box-sub");
//   var x_b = document.getElementsByClassName("circle-button");
//   if (n > x.length) {
//     slideIndex = 1;
//   }
//   if (n < 1) {
//     slideIndex = x.length;
//   }
//   for (i = 0; i < x.length; i++) {
//     x[i].classList.remove("show");
//     x_b[i].classList.remove("show");
//     x[i].children[0].classList.remove("resize-text-min-call");
//     x[i].children[1].classList.remove("resize-text-min-call");
//     x[i].children[0].classList.remove("resize-text-min");
//     x[i].children[1].classList.remove("resize-text-min");
//   }
//   x[slideIndex - 1].classList.add("show");
//   x_b[slideIndex - 1].classList.add("show");
//   x[slideIndex - 1].children[0].classList.add("resize-text-min-call");
//   x[slideIndex - 1].children[1].classList.add("resize-text-min-call");
//   //$(".resize-text-min-call").textfit('bestfit');
// }
