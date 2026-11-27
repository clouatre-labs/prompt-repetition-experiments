<?php
namespace App;
abstract class BaseCounter {
    abstract public function reset(): void;
}
class Counter extends BaseCounter {
    private int $count = 0;
    public function increment(int $by = 1): void {
        $this->count += $by;
    }
    public function reset(): void {
        $this->count = 0;
    }
}
