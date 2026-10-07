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
    return "Unknown Card Network"

def _find_candidates(text: str) -> list:
    """Splits separator-joined digit runs into the longest Luhn-valid 13-19 digit spans of whole digit groups."""
    candidates = []
    for run in re.finditer(r'\d(?:[ -]*\d)*', text):
        run_text = run.group()
        groups = [m.span() for m in re.finditer(r'\d+', run_text)]
        start = 0
        while start < len(groups):
            for end in range(len(groups) - 1, start - 1, -1):
                candidate = run_text[groups[start][0]:groups[end][1]]
                digit_count = sum(c.isdigit() for c in candidate)
                if 13 <= digit_count <= 19 and is_luhn_valid(candidate):
                    candidates.append(candidate)
                    start = end + 1
                    break
            else:
                start += 1
    return candidates

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
    found_potentials = _find_candidates(text)
    
    valid_cards = []
    processed = set()

    for potential in found_potentials:
        cleaned_number = re.sub(r'\D', '', potential)
        if 13 <= len(cleaned_number) <= 19 and cleaned_number not in processed:
            if is_luhn_valid(cleaned_number):
                processed.add(cleaned_number)
                valid_cards.append({
                    "original": potential,
                    "cleaned": cleaned_number,
                    "brand": detect_card_brand(cleaned_number),
                    "style": analyze_context(potential)
                })
    return valid_cards

