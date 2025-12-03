def validate_phone_number(phone):
    # Very simple validator: ensure digits and length 9-13
    s = ''.join(c for c in str(phone) if c.isdigit())
    return 9 <= len(s) <= 13

