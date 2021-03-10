
function ready() {
    $(".resize-text").textfit('bestfit_min');
    $(".resize-text-min").textfit('bestfit_min');
    $(".resize-text-min-call").textfit('bestfit');
    if (window.location.hash === "#dashboard") {
        onClickTableTab("Dashboard");
    }
    else if (window.location.hash === "#jupyterlab") {
        onClickTableTab("JupyterLab");
    }
    else if (localStorage.getItem('tab') != null) {
        onClickTableTab(localStorage.getItem('tab'));
    }
}
function onClickTableTab(value) {
  if ( value == "JupyterLab" ) {
    $('.tab_Dashboard_div').removeClass('active');
    $('.tab_JupyterLab_div').addClass('active');
    $('#Dashboards-div').hide();
    $('#JupyterLabs-div').show();
    localStorage.setItem("tab", "JupyterLab");
  }
  else if ( value == "Dashboard" ) {
    $('.tab_JupyterLab_div').removeClass('active');
    $('.tab_Dashboard_div').addClass('active');
    $('#JupyterLabs-div').hide();
    $('#Dashboards-div').show();
    localStorage.setItem("tab", "Dashboard");
  }
}

