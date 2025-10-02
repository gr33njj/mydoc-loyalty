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
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// ВАЖНО: Сначала загружаем Bitrix, потом работаем с сессией
require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

// Убеждаемся что сессия запущена
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Получаем токен из POST
$input = json_decode(file_get_contents('php://input'), true);
$token = $input['token'] ?? '';

if (empty($token)) {
    echo json_encode(['success' => false, 'error' => 'Token required'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Проверяем токен в файле (а не в сессии, т.к. запрос приходит от другого сервера)
$tokenDir = $_SERVER["DOCUMENT_ROOT"] . '/upload/loyalty_tokens/';
$tokenFile = $tokenDir . $token . '.json';

// Очищаем старые токены (> 10 минут)
if (is_dir($tokenDir)) {
    $files = glob($tokenDir . '*.json');
    foreach ($files as $file) {
        if (filemtime($file) < time() - 600) {
            @unlink($file);
        }
    }
}

if (!file_exists($tokenFile)) {
    echo json_encode(['success' => false, 'error' => 'Invalid token'], JSON_UNESCAPED_UNICODE);
    exit;
}

$tokenData = json_decode(file_get_contents($tokenFile), true);

// Проверяем срок действия
if ($tokenData['expires_at'] < time()) {
    unlink($tokenFile);
    echo json_encode(['success' => false, 'error' => 'Token expired'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Удаляем использованный токен (одноразовый)
unlink($tokenFile);

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

