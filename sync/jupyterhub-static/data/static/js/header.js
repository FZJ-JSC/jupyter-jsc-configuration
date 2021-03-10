document.getElementById("navbarbtn-links").addEventListener("mouseover", function(){ menu_hover("navbarbtn-links", "navbarmenu-links", "thenavbar"); });
function menu_hover(myId, myMenuId, parentMenuId){
  var me = document.getElementById(myId);
  var myMenu = document.getElementById(myMenuId);
  var parentMenu = document.getElementById(parentMenuId);
  for (var i = 0; i < parentMenu.children[0].children.length; i++){
    child = parentMenu.children[0].children[i].children[1];
    if ( child && child.classList.contains("menu-box") ) {
      if ( myMenu != null && child.id == myMenu.id ) {
        child.classList.add("show-header");
      } else {
        child.classList.remove("show-header");
      }
    }
  }
}

document.getElementById("navbarbtn-links").addEventListener("mouseout", function(){ menu_hover_off("navbarmenu-links"); });
function menu_hover_off(myMenuId) {
  var myMenu = document.getElementById(myMenuId);
  if ( myMenu ) {
    myMenu.classList.remove("show-header");
    for (var i = 0; i < myMenu.children[0].children.length; i++) {
      var child = myMenu.children[0].children[i].children[1];
      child.classList.remove("show-header");
    }
  }
}

document.getElementById("navbarbtn-links-1").addEventListener("mouseover", function(){ submenu_hover("navbarbtn-links-1", "navbarmenu-links-1", "navbarmenu-links"); });
document.getElementById("navbarbtn-links-2").addEventListener("mouseover", function(){ submenu_hover("navbarbtn-links-2", "navbarmenu-links-2", "navbarmenu-links"); });
document.getElementById("navbarbtn-links-3").addEventListener("mouseover", function(){ submenu_hover("navbarbtn-links-3", "navbarmenu-links-3", "navbarmenu-links"); });

function submenu_hover(myId, myMenuId, parentMenuId){
  var me = document.getElementById(myId);
  var myMenu = document.getElementById(myMenuId);
  var parentMenu = document.getElementById(parentMenuId);
  for (var i = 0; i < parentMenu.children[0].children.length; i++){
    child = parentMenu.children[0].children[i].children[1];
    if ( child.id == myMenu.id ) {
      child.style.top = i*30+"px";
      child.classList.add("show-header");
    } else {
      child.classList.remove("show-header");
    }
  }
}
