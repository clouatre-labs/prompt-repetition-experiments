<?php
namespace App;
interface Greeter {
    public function greet(): string;
}
class EnglishGreeter implements Greeter {
    public function greet(): string {
        return "hello";
    }
}
