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
    
    $bonusBalance = 0;
    $bonuses_stack = [];
    
    // Если есть JSON с бонусами - рассчитываем баланс
    if (!empty($arUser['UF_USER__BONUSES_JSON'])) {
        $bonus_list = json_decode($arUser['UF_USER__BONUSES_JSON'], true);
        
        foreach (($bonus_list ?? []) as $bonus) {
            // Начисление
            if ($bonus['RecordType'] === 'Receipt') {
                // Проверяем нет ли на дату текущего начисления просроченных прежних начислений
                while ($stack_bonus = array_pop($bonuses_stack)) {
                    if (!empty($stack_bonus['WRITE_OFF_DATE']) && $stack_bonus['WRITE_OFF_DATE'] < strtotime($bonus['Period'])) {
                        $bonusBalance -= $stack_bonus['Накопление'];
                    } else {
                        array_push($bonuses_stack, $stack_bonus);
                        break;
                    }
                }
                
                $bonusBalance += $bonus['Накопление'];
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
            }
        }
        
        // Проверяем просроченные начисления на текущую дату
        if (!empty($bonuses_stack)) {
            while ($stack_bonus = array_pop($bonuses_stack)) {
                if (!empty($stack_bonus['WRITE_OFF_DATE']) && $stack_bonus['WRITE_OFF_DATE'] < time()) {
                    $bonusBalance -= $stack_bonus['Накопление'];
                }
            }
        }
    }
    
    echo json_encode([
        'success' => true,
        'user_id' => $userId,
        'bonus_balance' => $bonusBalance
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>

