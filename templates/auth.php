<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login / Signup - Caleminder</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="styles.css"> 
</head>
<body class="flex justify-center items-center h-screen">

  <div id="signIn" class="bg-gray-800 p-8 rounded-lg shadow-lg w-96">
    <h1 class="text-2xl font-bold mb-4 text-center">Login</h1>
    <div id="signInError" class="text-red-500 text-sm mb-3 hidden"></div>
    <form id="signInForm" method="post" action="/auth">
      <input type="hidden" name="auth_type" value="signIn">
      <input type="email" name="email" placeholder="Email" class="w-full mb-3 p-2 rounded bg-gray-700 border border-gray-600" required>
      <input type="password" name="password" placeholder="Password" class="w-full mb-4 p-2 rounded bg-gray-700 border border-gray-600" required>
      <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded">Login</button>
    </form>
    <p class="mt-4 text-sm text-center">Don't have an account? 
      <a href="#" id="signUpButton" class="text-indigo-400 hover:underline">Sign up</a>
    </p>
  </div>

  <div id="signup" class="bg-gray-800 p-8 rounded-lg shadow-lg w-96" style="display:none;">
    <h1 class="text-2xl font-bold mb-4 text-center">Create Account</h1>
    <div id="signUpError" class="text-red-500 text-sm mb-3 hidden"></div>
    <form id="signUpForm" method="post" action="/auth">
      <input type="hidden" name="auth_type" value="signUp">
      <input type="text" name="firstname" placeholder="First Name" class="w-full mb-3 p-2 rounded bg-gray-700 border border-gray-600" required>
      <input type="text" name="lastname" placeholder="Last Name" class="w-full mb-3 p-2 rounded bg-gray-700 border border-gray-600" required>
      <input type="text" name="username" placeholder="Username" class="w-full mb-3 p-2 rounded bg-gray-700 border border-gray-600" required>
      <input type="email" name="email" placeholder="Email" class="w-full mb-3 p-2 rounded bg-gray-700 border border-gray-600" required>
      <input type="password" name="password" placeholder="Password" class="w-full mb-4 p-2 rounded bg-gray-700 border border-gray-600" required>
      <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded">Sign Up</button>
    </form>
    <p class="mt-4 text-sm text-center">Already have an account? 
      <a href="#" id="signInButton" class="text-indigo-400 hover:underline">Login</a>
    </p>
  </div>

  <script>
    // Get the elements by their IDs
    const signUpButton = document.getElementById('signUpButton');
    const signInButton = document.getElementById('signInButton');
    const signInForm = document.getElementById('signIn');
    const signUpForm = document.getElementById('signup');
    const signInFormElement = document.getElementById('signInForm');
    const signUpFormElement = document.getElementById('signUpForm');
    const signInError = document.getElementById('signInError');
    const signUpError = document.getElementById('signUpError');

    // Toggle between sign in and sign up
    if (signUpButton) {
      signUpButton.addEventListener('click', function(event) {
        event.preventDefault();
        signInForm.style.display = "none";
        signUpForm.style.display = "block";
        signInError.classList.add('hidden');
      });
    }

    if (signInButton) {
      signInButton.addEventListener('click', function(event) {
        event.preventDefault();
        signInForm.style.display = "block";
        signUpForm.style.display = "none";
        signUpError.classList.add('hidden');
      });
    }

    // Handle sign in form submission
    signInFormElement.addEventListener('submit', async function(event) {
      event.preventDefault();
      
      const formData = new FormData(signInFormElement);
      
      try {
        const response = await fetch('/auth', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
          // Redirect to main app
          window.location.href = '/index.html';
        } else {
          signInError.textContent = data.error || 'Sign in failed';
          signInError.classList.remove('hidden');
        }
      } catch (error) {
        console.error('Error:', error);
        signInError.textContent = 'An error occurred. Please try again.';
        signInError.classList.remove('hidden');
      }
    });

    // Handle sign up form submission
    signUpFormElement.addEventListener('submit', async function(event) {
      event.preventDefault();
      
      const formData = new FormData(signUpFormElement);
      
      try {
        const response = await fetch('/auth', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
          // Redirect to main app
          window.location.href = '/index.html';
        } else {
          signUpError.textContent = data.error || 'Sign up failed';
          signUpError.classList.remove('hidden');
        }
      } catch (error) {
        console.error('Error:', error);
        signUpError.textContent = 'An error occurred. Please try again.';
        signUpError.classList.remove('hidden');
      }
    });
  </script>

</body>
</html>