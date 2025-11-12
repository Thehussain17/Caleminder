// Get the elements by their new IDs
const signUpButton = document.getElementById('signUpButton');
const signInButton = document.getElementById('signInButton');
const signInForm = document.getElementById('signIn'); // This is the <div> wrapper
const signUpForm = document.getElementById('signup'); // This is the <div> wrapper

// When user clicks "Sign up" link
signUpButton.addEventListener('click', function(event) {
    event.preventDefault(); // Stop the link from jumping to "#"
    signInForm.style.display = "none";
    signUpForm.style.display = "block";
});

// When user clicks "Login" link
signInButton.addEventListener('click', function(event) {
    event.preventDefault(); // Stop the link from jumping to "#"
    signInForm.style.display = "block";
    signUpForm.style.display = "none";
});