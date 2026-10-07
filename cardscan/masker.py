from .validator import scan_text_advanced

def mask_card_number(original_match: str) -> str:
    """Masks digits while perfectly preserving the user's specific delimiter spacing layout."""
    digits = [d for d in original_match if d.isdigit()]
    unmasked_cutoff = len(digits) - 4 # Leave last 4 open
    
    digit_counter = 0
    masked_chars = []
    
    for char in original_match:
        if char.isdigit():
            if digit_counter < unmasked_cutoff:
                masked_chars.append('X')
            else:
                masked_chars.append(char)
            digit_counter += 1
        else:
            masked_chars.append(char) # Preserves user spaces or dashes perfectly
            
    return "".join(masked_chars)

def redact_text(text: str, known_brands_only: bool = False) -> str:
    """Scans raw blocks, calls validator core dependency, and safely scrubs leaked numbers."""
    valid_cards = scan_text_advanced(text, known_brands_only=known_brands_only)
    redacted_text = text
    
    for card in valid_cards:
        original_string = card["original"]
        masked_string = mask_card_number(original_string)
        redacted_text = redacted_text.replace(original_string, masked_string)
        
    return redacted_text

