<?php 

include 'connect.php';

// Handle Sign Up
if(isset($_POST['auth_type']) && $_POST['auth_type'] === 'signUp'){
    $firstName = $conn->real_escape_string($_POST['firstname']);
    $lastName = $conn->real_escape_string($_POST['lastname']);
    $email = $conn->real_escape_string($_POST['email']);
    $username = $conn->real_escape_string($_POST['username']);
    $password = md5($_POST['password']);

    // Check if email already exists
    $checkEmail = "SELECT * FROM users WHERE email='$email'";
    $result = $conn->query($checkEmail);
    
    if($result->num_rows > 0){
        echo "Error: Email Address Already Exists!";
        http_response_code(400);
    } else {
        // Insert new user
        $insertQuery = "INSERT INTO users(firstname, lastname, email, username, password) 
                        VALUES ('$firstName', '$lastName', '$email', '$username', '$password')";
        
        if($conn->query($insertQuery) === TRUE){
            session_start();
            $_SESSION['email'] = $email;
            echo "success";
            http_response_code(200);
        } else {
            echo "Error: " . $conn->error;
            http_response_code(500);
        }
    }
    exit();
}

// Handle Sign In
if(isset($_POST['auth_type']) && $_POST['auth_type'] === 'signIn'){
    $email = $conn->real_escape_string($_POST['email']);
    $password = md5($_POST['password']);
    
    $sql = "SELECT * FROM users WHERE email='$email' AND password='$password'";
    $result = $conn->query($sql);
    
    if($result->num_rows > 0){
        session_start();
        $row = $result->fetch_assoc();
        $_SESSION['email'] = $row['email'];
        $_SESSION['user_id'] = $row['id'];
        echo "success";
        http_response_code(200);
    } else {
        echo "Error: Incorrect Email or Password";
        http_response_code(401);
    }
    exit();
}

?>
