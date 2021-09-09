function getright(percent) {
  if (percent < 50) {
    return (percent * 180) / 50;
  }
  return 180;
}

function getleft(percent) {
  if (percent <= 50) {
    return 0;
  }
  return ((percent - 50) * 180) / 50;
}

function moveBarTo(progText) {
  moveBarToFull(progText, 0.8, false);
}

function moveBarToFull(progText, animationTime, setRed) {
  if (progText == 100) {
    animationTime = 0.1;
  }
  var pbright = document.getElementById("pbright");
  var pbleft = document.getElementById("pbleft");
  var progressLog = $("#progress-log");
  var srProgress = $("#sr-progress");

  pbleft_old = pbleft.style.getPropertyValue("--endlp");
  pbright_old = pbright.style.getPropertyValue("--endrp");
  if (pbleft_old.length == 0) {
    pbleft_old = "0deg";
  }
  if (pbright_old.length == 0) {
    pbright_old = "0deg";
  }
  //console.log("1: " + pbleft_old+ " - "+ pbright_old);
  if (pbleft_old == 0 || pbleft_old == "0deg") {
    pbleft.style.setProperty("--delay_start_left", new Date().getTime() / 1000);
    delay_left = animationTime;
  } else {
    delay_left =
      new Date().getTime() / 1000 -
      pbleft.style.getPropertyValue("--delay_start_left");
  }
  if (pbright_old == 0 || pbright_old == "0deg") {
    pbright.style.setProperty(
      "--delay_start_right",
      new Date().getTime() / 1000
    );
    delay_right = 0;
  } else {
    delay_right =
      new Date().getTime() / 1000 -
      pbright.style.getPropertyValue("--delay_start_right");
  }
  pbright_new = getright(progText);
  pbleft_new = getleft(progText);
  //console.log("2: " + pbleft_new+ " - "+ pbright_new);
  pbleft.style.setProperty("--startlp", pbleft_old);
  pbleft.style.setProperty("--endlp", pbleft_new + "deg");
  pbright.style.setProperty("--startrp", pbright_old);
  pbright.style.setProperty("--endrp", pbright_new + "deg");
  if (setRed) {
    pbleft.style.setProperty("border-color", "red");
    pbright.style.setProperty("border-color", "red");
  }
  if (pbright_new == 180 && pbright_old != "180deg" && pbleft_new > 0) {
    move_right = pbright_new - pbright_old.substring(0, pbright_old.length - 3);
    move_left = pbleft_new;
    //console.log("3: " + move_left + " - "+ move_right);
    duration_right = (animationTime * move_right) / (move_right + move_left);
    duration_left = (animationTime * move_left) / (move_right + move_left);
    delay_left = delay_left - (animationTime - duration_right);
    $("#pbright").css(
      "animation",
      "loading-rp " + duration_right + "s linear " + delay_right + "s forwards"
    );
    $("#pbleft").css(
      "animation",
      "loading-lp " + duration_left + "s linear " + delay_left + "s forwards"
    );
  } else {
    //console.log("Right: " + animationTime + " - " +delay_right);
    $("#pbright").css(
      "animation",
      "loading-rp " + animationTime + "s linear " + delay_right + "s forwards"
    );
    if (pbleft_new != 0) {
      $("#pbleft").css(
        "animation",
        "loading-lp " + animationTime + "s linear " + delay_left + "s forwards"
      );
    }
  }
  srProgress.text(progText + "%");
}
