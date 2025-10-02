<?php
/**
 * Файл для проверки токена авторизации
 * 
 * Путь установки: /local/api/verify_token.php
 * URL: https://mydoctorarmavir.ru/local/api/verify_token.php
 */

header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

// Получаем токен из POST
$input = json_decode(file_get_contents('php://input'), true);
$token = $input['token'] ?? '';

if (empty($token)) {
    echo json_encode(['success' => false, 'error' => 'Token required'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Проверяем токен в сессии
$sessionKey = 'LOYALTY_TOKEN_' . $token;

if (!isset($_SESSION[$sessionKey])) {
    echo json_encode(['success' => false, 'error' => 'Invalid token'], JSON_UNESCAPED_UNICODE);
    exit;
}

$tokenData = $_SESSION[$sessionKey];

// Проверяем срок действия
if ($tokenData['expires_at'] < time()) {
    unset($_SESSION[$sessionKey]);
    echo json_encode(['success' => false, 'error' => 'Token expired'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Удаляем использованный токен (одноразовый)
unset($_SESSION[$sessionKey]);

// Возвращаем данные пользователя
echo json_encode([
    'success' => true,
    'user' => [
        'bitrix_id' => $tokenData['user_id'],
        'email' => $tokenData['email'],
        'name' => $tokenData['name'],
        'last_name' => $tokenData['last_name']
    ]
], JSON_UNESCAPED_UNICODE);
?>

