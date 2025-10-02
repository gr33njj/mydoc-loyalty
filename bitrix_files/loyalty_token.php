<?php
/**
 * Файл для генерации токена авторизации в системе лояльности
 * 
 * Путь установки: /local/api/loyalty_token.php
 * URL: https://mydoctorarmavir.ru/local/api/loyalty_token.php
 */

// Разрешаем запросы с нашего домена
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

// Обработка preflight запроса
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

global $USER;

// Проверяем авторизацию
if (!$USER->IsAuthorized()) {
    echo json_encode([
        'success' => false,
        'error' => 'User not authorized'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Получаем данные пользователя
$userId = $USER->GetID();
$userEmail = $USER->GetEmail();
$userName = $USER->GetFirstName();
$userLastName = $USER->GetLastName();
$userLogin = $USER->GetLogin();

// Генерируем одноразовый токен (действует 2 минуты)
$token = md5($userId . time() . 'mydoc_loyalty_secret_2025');

// Сохраняем данные в сессию Bitrix
$_SESSION['LOYALTY_TOKEN_' . $token] = [
    'user_id' => $userId,
    'email' => $userEmail ?: $userLogin . '@mydoc.local',
    'name' => $userName,
    'last_name' => $userLastName,
    'created_at' => time(),
    'expires_at' => time() + 120 // 2 минуты
];

// Возвращаем токен
echo json_encode([
    'success' => true,
    'token' => $token,
    'user_id' => $userId,
    'email' => $userEmail ?: $userLogin . '@mydoc.local'
], JSON_UNESCAPED_UNICODE);
?>

