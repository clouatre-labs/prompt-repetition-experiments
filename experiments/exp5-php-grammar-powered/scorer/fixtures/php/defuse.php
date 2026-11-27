<?php
$total = 0;
$total += 5;
echo $total;
function spend(int $amount): int {
    global $total;
    $total = $total - $amount;
    return $total;
}
