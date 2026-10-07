import re

def is_luhn_valid(card_number: str) -> bool:
    """Verifies a card number string using the Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    digits.reverse()
    
    total_sum = 0
    for index, digit in enumerate(digits):
        if index % 2 == 1:  # Double every second digit
            doubled = digit * 2
            total_sum += doubled if doubled <= 9 else (doubled - 9)
        else:
            total_sum += digit
            
    return total_sum % 10 == 0

def scan_text_for_cc(text: str):
    """V1: Scans text for bounded credit card strings and validates them."""
    cc_pattern = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
    found_potentials = cc_pattern.findall(text)
    
    for potential in found_potentials:
        cleaned_number = re.sub(r'\D', '', potential)
        if is_luhn_valid(cleaned_number):
            print(f"⚠️ Flagged: Valid credit card layout found -> {potential}")

