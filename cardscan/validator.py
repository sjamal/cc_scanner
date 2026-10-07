import re

def is_luhn_valid(card_number: str) -> bool:
    """Verifies a card number string using the Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    digits.reverse()
    total_sum = 0
    for index, digit in enumerate(digits):
        if index % 2 == 1:
            total_sum += (digit * 2) if (digit * 2) <= 9 else ((digit * 2) - 9)
        else:
            total_sum += digit
    return total_sum % 10 == 0

def detect_card_brand(number: str) -> str:
    """Identifies the credit card network based on standard prefix ranges."""
    if number.startswith(('34', '37')) and len(number) == 15:
        return "American Express"
    elif number.startswith('4'):
        return "Visa"
    elif re.match(r'^5[1-5]|^2[2-7]', number):
        return "Mastercard"
    elif number.startswith('6011') or number.startswith('65'):
        return "Discover"
    elif re.match(r'^64[4-9]', number) or (number[:6].isdigit() and 622126 <= int(number[:6]) <= 622925):
        return "Discover"
    elif number[:4].isdigit() and 3528 <= int(number[:4]) <= 3589:
        return "JCB"
    elif re.match(r'^30[0-5]|^3[689]', number):
        return "Diners Club"
    elif number.startswith('62'):
        return "UnionPay"
    return "Unknown Card Network"

def analyze_context(original_match: str) -> str:
    """Deduces how the user formatted their input context."""
    if '-' in original_match and ' ' in original_match:
        return "Mixed Format (Dashes and Spaces)"
    elif '-' in original_match:
        return "Standard Dashes (e.g., XXXX-XXXX-XXXX-XXXX)"
    elif ' ' in original_match:
        return "Amex Style Spaces" if original_match.count(' ') == 2 else "Standard Spaces"
    return "Raw Continuous Block (No separators)"

def scan_text_advanced(text: str) -> list:
    """V2: Scans text for numbers hidden anywhere, returning structural context dicts."""
    cc_pattern = re.compile(r'(?:\d[ -]*?){13,19}')
    found_potentials = cc_pattern.findall(text)
    
    valid_cards = []
    processed = set()

    for potential in found_potentials:
        cleaned_number = re.sub(r'\D', '', potential)
        if 15 <= len(cleaned_number) <= 16 and cleaned_number not in processed:
            if is_luhn_valid(cleaned_number):
                processed.add(cleaned_number)
                valid_cards.append({
                    "original": potential,
                    "cleaned": cleaned_number,
                    "brand": detect_card_brand(cleaned_number),
                    "style": analyze_context(potential)
                })
    return valid_cards

