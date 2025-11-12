<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login / Signup - Caleminder</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; }
    .glass {
      background: rgba(31, 41, 55, 0.6);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
  </style>
</head>

<body class="bg-gray-900 text-white flex justify-center items-center min-h-screen px-4">

  <!-- LOGIN CARD -->
  <div id="signIn" class="glass p-8 rounded-2xl shadow-2xl w-full max-w-md transition-all">
    <h1 class="text-3xl font-bold mb-4 text-center text-white">Welcome Back</h1>
    <p class="text-center text-gray-400 mb-6 text-sm">Sign in to continue to Caleminder</p>

    <div id="signInError" class="text-red-400 text-sm mb-3 hidden"></div>

    <form id="signInForm" method="post" action="/auth" class="space-y-4">
      <input type="hidden" name="auth_type" value="signIn">

      <input type="email" name="email" placeholder="Email"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <input type="password" name="password" placeholder="Password"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <button type="submit"
        class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-lg transition focus:ring-2 focus:ring-indigo-500 focus:outline-none">
        Login
      </button>
    </form>

    <p class="mt-6 text-sm text-center text-gray-400">
      Don't have an account?
      <a href="#" id="signUpButton" class="text-indigo-400 hover:text-indigo-300 font-medium">Sign up</a>
    </p>
  </div>

  <!-- SIGNUP CARD -->
  <div id="signup" class="glass p-8 rounded-2xl shadow-2xl w-full max-w-md transition-all hidden">
    <h1 class="text-3xl font-bold mb-4 text-center text-white">Create Account</h1>
    <p class="text-center text-gray-400 mb-6 text-sm">Join Caleminder today</p>

    <div id="signUpError" class="text-red-400 text-sm mb-3 hidden"></div>

    <form id="signUpForm" method="post" action="/auth" class="space-y-4">
      <input type="hidden" name="auth_type" value="signUp">

      <input type="text" name="firstname" placeholder="First Name"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <input type="text" name="lastname" placeholder="Last Name"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <input type="text" name="username" placeholder="Username"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <input type="email" name="email" placeholder="Email"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <input type="password" name="password" placeholder="Password"
        class="w-full p-3 rounded-lg bg-gray-800/60 border border-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        required>

      <button type="submit"
        class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-lg transition focus:ring-2 focus:ring-indigo-500 focus:outline-none">
        Sign Up
      </button>
    </form>

    <p class="mt-6 text-sm text-center text-gray-400">
      Already have an account?
      <a href="#" id="signInButton" class="text-indigo-400 hover:text-indigo-300 font-medium">Login</a>
    </p>
  </div>

  <script>
    // Get elements
    const signUpButton = document.getElementById('signUpButton');
    const signInButton = document.getElementById('signInButton');
    const signInForm = document.getElementById('signIn');
    const signUpForm = document.getElementById('signup');
    const signInFormElement = document.getElementById('signInForm');
    const signUpFormElement = document.getElementById('signUpForm');
    const signInError = document.getElementById('signInError');
    const signUpError = document.getElementById('signUpError');

    // Toggle forms
    if (signUpButton) {
      signUpButton.addEventListener('click', function (e) {
        e.preventDefault();
        signInForm.style.display = "none";
        signUpForm.style.display = "block";
        signInError.classList.add('hidden');
      });
    }

    if (signInButton) {
      signInButton.addEventListener('click', function (e) {
        e.preventDefault();
        signInForm.style.display = "block";
        signUpForm.style.display = "none";
        signUpError.classList.add('hidden');
      });
    }

    // Handle Sign In
    signInFormElement.addEventListener('submit', async function (event) {
      event.preventDefault();
      const formData = new FormData(signInFormElement);

      try {
        const response = await fetch('/auth', { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
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

    // Handle Sign Up
    signUpFormElement.addEventListener('submit', async function (event) {
      event.preventDefault();
      const formData = new FormData(signUpFormElement);

      try {
        const response = await fetch('/auth', { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
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
