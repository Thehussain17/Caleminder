<?php
// profile.php - update user profile via POST
// Connect to database and ensure session is started
include_once 'connect.php';
session_start();

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Determine user id: prefer session value, fall back to posted id
    $id = isset($_SESSION['user_id']) ? intval($_SESSION['user_id']) : (isset($_POST['id']) ? intval($_POST['id']) : 0);

    if ($id <= 0) {
        echo "❌ Error: No user id provided or in session.";
        exit();
    }

    // Sanitize inputs
    $firstname = isset($_POST['firstname']) ? $conn->real_escape_string($_POST['firstname']) : '';
    $lastname = isset($_POST['lastname']) ? $conn->real_escape_string($_POST['lastname']) : '';
    $username = isset($_POST['username']) ? $conn->real_escape_string($_POST['username']) : '';

    if ($firstname === '' || $lastname === '' || $username === '') {
        echo "❌ Error: firstname, lastname and username are required.";
        exit();
    }

    // If a new password was provided, hash it and include in update
    if (!empty($_POST['password'])) {
        // Use PHP password_hash for secure storage
        $hashed_password = password_hash($_POST['password'], PASSWORD_DEFAULT);

        $stmt = $conn->prepare("UPDATE users SET firstname=?, lastname=?, username=?, password=? WHERE id=?");
        $stmt->bind_param("ssssi", $firstname, $lastname, $username, $hashed_password, $id);
    } else {
        $stmt = $conn->prepare("UPDATE users SET firstname=?, lastname=?, username=? WHERE id=?");
        $stmt->bind_param("sssi", $firstname, $lastname, $username, $id);
    }

    if ($stmt->execute()) {
        echo "✅ User updated successfully!";
    } else {
        if ($conn->errno == 1062) {
            echo "❌ Error: This username ('" . htmlspecialchars($username) . "') or email is already taken.";
        } else {
            echo "❌ Error updating user: " . $conn->error;
        }
    }



    $stmt->close();
}
?>