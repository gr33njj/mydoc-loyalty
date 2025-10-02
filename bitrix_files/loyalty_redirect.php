<?php
/**
 * Промежуточная страница для SSO авторизации
 * 
 * Путь установки: /local/pages/loyalty_redirect.php
 * URL: https://mydoctorarmavir.ru/local/pages/loyalty_redirect.php
 * 
 * Эта страница:
 * 1. Проверяет авторизацию в Bitrix
 * 2. Генерирует токен
 * 3. Редиректит на it-mydoc.ru с токеном
 */

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

// Убеждаемся что сессия запущена
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

global $USER;

// Проверяем авторизацию
if (!$USER->IsAuthorized()) {
    // Если не авторизован - редирект на авторизацию Bitrix
    LocalRedirect('/auth/?backurl=' . urlencode('/local/pages/loyalty_redirect.php'));
    exit;
}

// Получаем данные пользователя
$userId = $USER->GetID();
$userEmail = $USER->GetEmail();
$userName = $USER->GetFirstName();
$userLastName = $USER->GetLastName();
$userLogin = $USER->GetLogin();

// Генерируем токен
$token = md5($userId . time() . 'mydoc_loyalty_secret_2025');

// Сохраняем в сессию
$_SESSION['LOYALTY_TOKEN_' . $token] = [
    'user_id' => $userId,
    'email' => $userEmail ?: $userLogin . '@mydoc.local',
    'name' => $userName,
    'last_name' => $userLastName,
    'created_at' => time(),
    'expires_at' => time() + 300 // 5 минут
];

// Редирект на it-mydoc.ru с токеном
$redirectUrl = 'https://it-mydoc.ru/auth/sso?token=' . $token;
header('Location: ' . $redirectUrl);
exit;
?>

