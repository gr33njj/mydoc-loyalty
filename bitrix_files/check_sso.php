<?php
/**
 * Диагностический файл для проверки SSO
 * 
 * Установите в: /local/api/check_sso.php
 * Откройте: https://mydoctorarmavir.ru/local/api/check_sso.php
 */

header('Content-Type: text/html; charset=utf-8');

echo "<h1>🔍 Диагностика SSO</h1>";

// 1. Проверяем путь к Bitrix
echo "<h2>1. Путь к Bitrix:</h2>";
echo "<pre>" . $_SERVER["DOCUMENT_ROOT"] . "</pre>";

// 2. Проверяем наличие файлов
echo "<h2>2. Проверка файлов:</h2>";

$files = [
    'loyalty_redirect.php' => $_SERVER["DOCUMENT_ROOT"] . "/local/pages/loyalty_redirect.php",
    'verify_token.php' => $_SERVER["DOCUMENT_ROOT"] . "/local/api/verify_token.php"
];

foreach ($files as $name => $path) {
    echo "<strong>$name:</strong><br>";
    
    if (file_exists($path)) {
        echo "✅ Существует: <code>$path</code><br>";
        
        // Проверяем наличие session_start()
        $content = file_get_contents($path);
        if (strpos($content, 'session_start()') !== false) {
            echo "✅ Содержит session_start()<br>";
            
            // Показываем строку с session_start
            $lines = explode("\n", $content);
            foreach ($lines as $num => $line) {
                if (strpos($line, 'session_start') !== false) {
                    $lineNum = $num + 1;
                    echo "📍 Строка $lineNum: <code>" . htmlspecialchars($line) . "</code><br>";
                }
            }
        } else {
            echo "❌ НЕ содержит session_start() - ФАЙЛ УСТАРЕЛ!<br>";
        }
        
        // Показываем размер и дату изменения
        echo "📊 Размер: " . filesize($path) . " байт<br>";
        echo "📅 Изменен: " . date('Y-m-d H:i:s', filemtime($path)) . "<br>";
        
    } else {
        echo "❌ НЕ СУЩЕСТВУЕТ: <code>$path</code><br>";
    }
    
    echo "<br>";
}

// 3. Проверяем сессию
echo "<h2>3. Проверка сессии:</h2>";

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

if (session_status() === PHP_SESSION_NONE) {
    session_start();
    echo "✅ Сессия запущена вручную<br>";
} else {
    echo "✅ Сессия уже активна (запущена Bitrix)<br>";
}

echo "📋 Session ID: " . session_id() . "<br>";
echo "📋 Session status: " . session_status() . "<br>";

// 4. Проверяем авторизацию
echo "<h2>4. Проверка авторизации:</h2>";

global $USER;

if ($USER->IsAuthorized()) {
    echo "✅ Пользователь авторизован<br>";
    echo "👤 ID: " . $USER->GetID() . "<br>";
    echo "📧 Email: " . $USER->GetEmail() . "<br>";
    echo "👤 Имя: " . $USER->GetFirstName() . " " . $USER->GetLastName() . "<br>";
} else {
    echo "❌ Пользователь НЕ авторизован<br>";
    echo "⚠️ Сначала авторизуйтесь на сайте!<br>";
}

// 5. Тест создания токена
echo "<h2>5. Тест создания токена:</h2>";

if ($USER->IsAuthorized()) {
    $testToken = md5($USER->GetID() . time() . 'test');
    $_SESSION['TEST_TOKEN_' . $testToken] = [
        'user_id' => $USER->GetID(),
        'created_at' => time()
    ];
    
    echo "✅ Тестовый токен создан: <code>$testToken</code><br>";
    echo "✅ Сохранен в сессию: <code>\$_SESSION['TEST_TOKEN_$testToken']</code><br>";
    
    // Проверяем что токен сохранился
    if (isset($_SESSION['TEST_TOKEN_' . $testToken])) {
        echo "✅ Токен успешно читается из сессии!<br>";
        echo "📋 Данные: <pre>" . print_r($_SESSION['TEST_TOKEN_' . $testToken], true) . "</pre>";
    } else {
        echo "❌ Токен НЕ сохранился в сессию!<br>";
    }
} else {
    echo "⚠️ Нужна авторизация для теста токена<br>";
}

echo "<hr>";
echo "<h2>📝 Инструкция по обновлению:</h2>";
echo "<pre>";
echo "cd " . $_SERVER["DOCUMENT_ROOT"] . "/local/pages/\n";
echo "wget -O loyalty_redirect.php https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/loyalty_redirect.php\n\n";
echo "cd " . $_SERVER["DOCUMENT_ROOT"] . "/local/api/\n";
echo "wget -O verify_token.php https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/verify_token.php\n";
echo "</pre>";

?>

