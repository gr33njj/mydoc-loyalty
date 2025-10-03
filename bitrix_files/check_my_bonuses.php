<?php
/**
 * Скрипт для проверки бонусов текущего авторизованного пользователя
 * 
 * Путь установки: /local/api/check_my_bonuses.php
 * URL: https://mydoctorarmavir.ru/local/api/check_my_bonuses.php
 * 
 * Откройте этот URL в браузере БУДУЧИ АВТОРИЗОВАННЫМ в Bitrix
 */

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

header('Content-Type: application/json; charset=utf-8');

global $USER;

// Проверяем авторизацию
if (!$USER->IsAuthorized()) {
    echo json_encode([
        'error' => 'Вы не авторизованы! Войдите на сайт mydoctorarmavir.ru сначала.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

$userId = $USER->GetID();
$userEmail = $USER->GetEmail();

// Получаем данные пользователя
$rsUser = CUser::GetList(
    [], 
    [], 
    ['ID' => $userId], 
    ['SELECT' => ['ID', 'LOGIN', 'EMAIL', 'NAME', 'LAST_NAME', 'UF_USER__BONUSES_JSON']]
);

$arUser = $rsUser->Fetch();

if (!$arUser) {
    echo json_encode([
        'error' => 'Пользователь не найден'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Декодируем JSON с бонусами
$bonus_list = [];
$bonus_json_raw = $arUser['UF_USER__BONUSES_JSON'];

if (!empty($bonus_json_raw)) {
    $bonus_list = json_decode($bonus_json_raw, true);
}

// Выводим информацию
echo json_encode([
    'success' => true,
    'user_info' => [
        'id' => $arUser['ID'],
        'login' => $arUser['LOGIN'],
        'email' => $arUser['EMAIL'],
        'name' => $arUser['NAME'],
        'last_name' => $arUser['LAST_NAME']
    ],
    'bonuses_field_exists' => isset($arUser['UF_USER__BONUSES_JSON']),
    'bonuses_json_empty' => empty($bonus_json_raw),
    'bonuses_json_length' => strlen($bonus_json_raw ?? ''),
    'bonuses_count' => count($bonus_list),
    'bonuses_raw' => $bonus_json_raw,
    'bonuses_parsed' => $bonus_list,
    'instruction' => [
        'step1' => 'Скопируйте ваш ID: ' . $arUser['ID'],
        'step2' => 'Используйте этот ID для тестирования API',
        'step3' => 'curl -X POST https://mydoctorarmavir.ru/local/api/get_bonuses.php -H "Content-Type: application/json" -d \'{"user_id": ' . $arUser['ID'] . '}\'',
        'check_bitrix_page' => 'Сравните с https://mydoctorarmavir.ru/personal/bonuses/'
    ]
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>

