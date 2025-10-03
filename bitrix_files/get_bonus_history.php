<?php
/**
 * API для получения истории бонусных транзакций пользователя
 * 
 * Путь установки: /local/api/get_bonus_history.php
 * URL: https://mydoctorarmavir.ru/local/api/get_bonus_history.php
 * 
 * Параметры:
 *   - user_id (int) - ID пользователя в Bitrix
 *   - limit (int) - Количество записей (по умолчанию 50)
 * 
 * Возвращает:
 *   - success (bool)
 *   - transactions (array) - Массив транзакций
 *   - total (int) - Общее количество транзакций
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

// Получаем параметры
$userId = null;
$limit = 50;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $userId = $input['user_id'] ?? null;
    $limit = intval($input['limit'] ?? 50);
} else {
    $userId = $_GET['user_id'] ?? null;
    $limit = intval($_GET['limit'] ?? 50);
}

if (empty($userId)) {
    echo json_encode([
        'success' => false, 
        'error' => 'user_id required'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    // Получаем данные пользователя с полем UF_USER__BONUSES_JSON
    $rsUser = CUser::GetList(
        [], 
        [], 
        ['ID' => $userId], 
        ['SELECT' => ['ID', 'UF_USER__BONUSES_JSON']]
    );
    
    $arUser = $rsUser->Fetch();
    
    if (!$arUser) {
        throw new Exception('Пользователь не найден');
    }
    
    $transactions = [];
    $bonusBalance = 0;
    $bonuses_stack = [];
    
    // Если есть JSON с бонусами - формируем историю
    if (!empty($arUser['UF_USER__BONUSES_JSON'])) {
        $bonus_list = json_decode($arUser['UF_USER__BONUSES_JSON'], true);
        
        foreach (($bonus_list ?? []) as $bonus) {
            // Начисление
            if ($bonus['RecordType'] === 'Receipt') {
                // Проверяем нет ли на дату текущего начисления просроченных прежних начислений
                while ($stack_bonus = array_pop($bonuses_stack)) {
                    if (!empty($stack_bonus['WRITE_OFF_DATE']) && $stack_bonus['WRITE_OFF_DATE'] < strtotime($bonus['Period'])) {
                        $bonusBalance -= $stack_bonus['Накопление'];
                        $transactions[] = [
                            'date' => date('Y-m-d\TH:i:s', $stack_bonus['WRITE_OFF_DATE']),
                            'type' => 'expiration',
                            'amount' => round($stack_bonus['Накопление'], 2),
                            'balance' => round($bonusBalance, 2),
                            'description' => 'Истек срок действия бонусов'
                        ];
                    } else {
                        array_push($bonuses_stack, $stack_bonus);
                        break;
                    }
                }
                
                $bonusBalance += $bonus['Накопление'];
                $transactions[] = [
                    'date' => date('Y-m-d\TH:i:s', strtotime($bonus['Period'])),
                    'type' => 'accrual',
                    'amount' => round($bonus['Накопление'], 2),
                    'balance' => round($bonusBalance, 2),
                    'description' => 'Начисление бонусов',
                    'expires_at' => !empty($bonus['WRITE_OFF_DATE']) ? date('Y-m-d\TH:i:s', $bonus['WRITE_OFF_DATE']) : null,
                    'valid_days' => $bonus['WRITE_OFF_DAYS'] ?? null
                ];
                array_push($bonuses_stack, $bonus);
                
            // Списание
            } elseif ($bonus['RecordType'] === 'Expense') {
                $bonusBalance -= $bonus['Накопление'];
                $bonus_balance_to_write_off = $bonus['Накопление'];
                
                $counter = 0;
                while ($stack_bonus = array_pop($bonuses_stack)) {
                    $counter++;
                    
                    // Проверяем не просрочен ли бонус
                    if (!empty($stack_bonus['WRITE_OFF_DATE']) && $stack_bonus['WRITE_OFF_DATE'] < strtotime($bonus['Period'])) {
                        $bonusBalance -= $stack_bonus['Накопление'];
                        $transactions[] = [
                            'date' => date('Y-m-d\TH:i:s', strtotime($bonus['Period'])),
                            'type' => 'expiration',
                            'amount' => round($stack_bonus['Накопление'], 2),
                            'balance' => round($bonusBalance, 2),
                            'description' => 'Истек срок действия бонусов'
                        ];
                    } else {
                        // Если в начислении баллов больше чем нужно списать
                        if ($stack_bonus['Накопление'] > $bonus_balance_to_write_off) {
                            $stack_bonus['Накопление'] -= $bonus_balance_to_write_off;
                            $bonus_balance_to_write_off = 0;
                            array_push($bonuses_stack, $stack_bonus);
                        }
                        // Если баллы совпадают
                        if ($stack_bonus['Накопление'] === $bonus_balance_to_write_off) {
                            $bonus_balance_to_write_off = 0;
                        } else {
                            // Если баллов меньше
                            $bonus_balance_to_write_off -= $stack_bonus['Накопление'];
                        }
                    }
                    
                    if ($bonus_balance_to_write_off <= 0) break;
                    if ($counter > 100000) {
                        throw new Exception('Ошибка в расчете бонусов');
                    }
                }
                
                $transactions[] = [
                    'date' => date('Y-m-d\TH:i:s', strtotime($bonus['Period'])),
                    'type' => 'deduction',
                    'amount' => round($bonus['Накопление'], 2),
                    'balance' => round($bonusBalance, 2),
                    'description' => 'Списание бонусов'
                ];
            }
        }
        
        // Проверяем просроченные начисления на текущую дату
        if (!empty($bonuses_stack)) {
            while ($stack_bonus = array_pop($bonuses_stack)) {
                if (!empty($stack_bonus['WRITE_OFF_DATE']) && $stack_bonus['WRITE_OFF_DATE'] < time()) {
                    $bonusBalance -= $stack_bonus['Накопление'];
                    $transactions[] = [
                        'date' => date('Y-m-d\TH:i:s', $stack_bonus['WRITE_OFF_DATE']),
                        'type' => 'expiration',
                        'amount' => round($stack_bonus['Накопление'], 2),
                        'balance' => round($bonusBalance, 2),
                        'description' => 'Истек срок действия бонусов'
                    ];
                }
            }
        }
    }
    
    // Сортируем по дате (новые сверху)
    usort($transactions, function($a, $b) {
        return strtotime($b['date']) - strtotime($a['date']);
    });
    
    // Применяем limit
    $total = count($transactions);
    $transactions = array_slice($transactions, 0, $limit);
    
    echo json_encode([
        'success' => true,
        'user_id' => $userId,
        'transactions' => $transactions,
        'total' => $total,
        'current_balance' => round($bonusBalance, 2)
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>

