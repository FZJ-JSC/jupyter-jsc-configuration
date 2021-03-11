document.getElementById("ampel-jupyter-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-jupyter"); });
document.getElementById("ampel-juwels-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-juwels"); });
document.getElementById("ampel-jureca-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-jureca"); });
document.getElementById("ampel-jusuf-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-jusuf"); });
document.getElementById("ampel-hdfml-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-hdfml"); });
document.getElementById("ampel-deep-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-deep"); });
document.getElementById("ampel-hdfcloud-img").addEventListener("mouseout", function(){ ampel_hover_off("ampel-hdfcloud"); });
function ampel_hover_off(spanId){
  document.getElementById(spanId).classList.remove("ampel-span-show");
}

document.getElementById("ampel-jupyter-img").addEventListener("mouseover", function(){ ampel_hover("ampel-jupyter"); });
document.getElementById("ampel-juwels-img").addEventListener("mouseover", function(){ ampel_hover("ampel-juwels"); });
document.getElementById("ampel-jureca-img").addEventListener("mouseover", function(){ ampel_hover("ampel-jureca"); });
document.getElementById("ampel-jusuf-img").addEventListener("mouseover", function(){ ampel_hover("ampel-jusuf"); });
document.getElementById("ampel-hdfml-img").addEventListener("mouseover", function(){ ampel_hover("ampel-hdfml"); });
document.getElementById("ampel-deep-img").addEventListener("mouseover", function(){ ampel_hover("ampel-deep"); });
document.getElementById("ampel-hdfcloud-img").addEventListener("mouseover", function(){ ampel_hover("ampel-hdfcloud"); });
function ampel_hover(spanId){
  var el = document.getElementById(spanId);
  if( el.innerText != "" ){
    document.getElementById(spanId).classList.add("ampel-span-show");
  }
}

