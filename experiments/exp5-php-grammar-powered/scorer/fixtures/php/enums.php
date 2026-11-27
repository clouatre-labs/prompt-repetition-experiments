<?php
namespace App;
interface HasLabel {
    public function label(): string;
}
enum Suit: string implements HasLabel {
    case Hearts = "H";
    case Spades = "S";
    public function label(): string {
        return $this->value;
    }
}
