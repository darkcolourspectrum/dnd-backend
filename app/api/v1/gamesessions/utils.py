import string
import random

def generate_session_id(length=8):
    # Генерируем случайный айдишник
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))