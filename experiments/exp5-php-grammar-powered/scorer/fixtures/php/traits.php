<?php
namespace App;
trait Loggable {
    private array $log = [];
    public function log(string $msg): void {
        $this->log[] = $msg;
    }
}
class Service {
    use Loggable;
}
