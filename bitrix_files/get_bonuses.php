<?php
/**
 * API для получения баланса бонусов пользователя
 * 
 * Путь установки: /local/api/get_bonuses.php
 * URL: https://mydoctorarmavir.ru/local/api/get_bonuses.php
 * 
 * Параметры:
 *   - user_id (int) - ID пользователя в Bitrix
 * 
 * Возвращает:
 *   - success (bool)
 *   - bonus_balance (float)
 *   - error (string) - если есть ошибка
 */

header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

// Получаем user_id
$userId = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $userId = $input['user_id'] ?? null;
} else {
    $userId = $_GET['user_id'] ?? null;
}

if (empty($userId)) {
    echo json_encode([
        'success' => false, 
        'error' => 'user_id required'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Загружаем модуль sale (если бонусы там хранятся)
\Bitrix\Main\Loader::includeModule('sale');

try {
    // ВАРИАНТ 1: Если бонусы хранятся в пользовательских полях
    $user = \Bitrix\Main\UserTable::getById($userId)->fetch();
    
    if (!$user) {
        throw new Exception('Пользователь не найден');
    }
    
    // Получаем бонусный баланс
    // ВНИМАНИЕ: Замените 'UF_BONUS_BALANCE' на реальное название поля в вашей системе!
    // Возможные варианты:
    // - UF_BONUS_POINTS
    // - UF_LOYALTY_BALANCE
    // - или другое пользовательское поле
    
    $bonusBalance = 0;
    
    // Попробуем найти поле с бонусами
    if (isset($user['UF_BONUS_BALANCE'])) {
        $bonusBalance = floatval($user['UF_BONUS_BALANCE']);
    } elseif (isset($user['UF_BONUS_POINTS'])) {
        $bonusBalance = floatval($user['UF_BONUS_POINTS']);
    } elseif (isset($user['UF_LOYALTY_BALANCE'])) {
        $bonusBalance = floatval($user['UF_LOYALTY_BALANCE']);
    }
    
    // ВАРИАНТ 2: Если бонусы хранятся в модуле Sale (счет покупателя)
    // Раскомментируйте если бонусы в Sale:
    /*
    $accounts = \Bitrix\Sale\Internals\UserAccountTable::getList([
        'filter' => [
            'USER_ID' => $userId,
            'CURRENCY' => 'RUB' // или другая валюта
        ]
    ])->fetch();
    
    if ($accounts) {
        $bonusBalance = floatval($accounts['CURRENT_BUDGET']);
    }
    */
    
    echo json_encode([
        'success' => true,
        'user_id' => $userId,
        'bonus_balance' => $bonusBalance,
        'currency' => 'RUB'
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>

