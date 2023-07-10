//show a confirmation and redirect to the delete profile script
function deleteProfile() {
    if (confirm("Do you really want to cancel your ticket?")) {
        location.href = '/deleteProfile.php';
    }
}

function toggle() {
    var x = document.getElementById("toggle")

    if (x.style.display === "none") {
        x.style.display = "block";
    } else {
        x.style.display = "none";
    }
    
}

document.getElementById("login-button-rounded").addEventListener("click", function() {
    document.getElementById("second-section").scrollIntoView({ behavior: 'smooth' });
  });


  function floatIn(element, duration) {
    var start = performance.now(); 
    var end = start + duration; 
    var startPosition = -200; 
    var endPosition = 0; 
    var easing = function(t) { return t<0.5 ? 4*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1 }; 
  
    function animate(time) {
      var progress = (time - start) / duration; 
      var position = startPosition + (endPosition - startPosition) * easing(progress); 
      element.style.left = position + '%'; 
      if (time < end) {
        requestAnimationFrame(animate); 
      }
    }
  
    requestAnimationFrame(animate); 
  }
  
  window.onload = function() {
    var animateMe = document.getElementById('welcome-message');
    floatIn(animateMe, 1200); 
  };