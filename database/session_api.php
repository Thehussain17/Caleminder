<?php
include_once 'connect.php';
session_start();
header('Content-Type: application/json'); //Tells to pass as json format

// If session has no user_id, return an error
if (!isset($_SESSION['user_id'])) {
    echo json_encode([
        "status" => "error",
        "message" => "No active session or user not logged in."
    ]);
    exit();
}

// Return only minimal required data
echo json_encode([
    "status" => "success",
    "user_id" => intval($_SESSION['user_id'])
]);

