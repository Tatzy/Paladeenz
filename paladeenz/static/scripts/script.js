function search(error) {
  //we need to add some logic here to account for the errors that the backend might give us
  if (error == "none") {
    console.log(error);
    window.location.href = window.parent.location + "?livematch=" + document.getElementById("fname").value;
  }
  else {
    console.log(error);
  }


}
var domain = "http://www.paladeenz.com";
function load_home() {
  window.location.href = domain;
}

