<?php
$bot_token = '7014256442:AAGXI7CXLfMGqDC4mp9vG9Exr-nozeoFD0I';
$data = $_GET;

// Проверка хэша
$check_hash = $data['hash'];
unset($data['hash']);

$data_check_arr = [];
foreach ($data as $key => $value) {
    $data_check_arr[] = $key . '=' . $value;
}
sort($data_check_arr);
$data_check_string = implode("\n", $data_check_arr);
$secret_key = hash('sha256', $bot_token, true);
$hash = hash_hmac('sha256', $data_check_string, $secret_key);

if (strcmp($hash, $check_hash) !== 0) {
    header('HTTP/1.1 401 Unauthorized');
    die('Invalid hash');
}

// Проверка времени (не старше 1 дня)
if ((time() - $data['auth_date']) > 86400) {
    header('HTTP/1.1 401 Unauthorized');
    die('Data outdated');
}

// Возвращаем данные пользователя
header('Content-Type: application/json');
echo json_encode([
    'id' => $data['id'],
    'first_name' => $data['first_name'],
    'last_name' => $data['last_name'] ?? '',
    'username' => $data['username'] ?? ''
]);