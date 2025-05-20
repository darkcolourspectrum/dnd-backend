import requests

BASE_URL = "http://localhost:8000"

def test_api():
    # 1. Авторизация
    login_data = {
        "email": "kirillkuzmin@mail.ru", 
        "password": "kirill1905",         
        "fingerprint": "test_device_123"  
    }
    
    print("Отправляем запрос на авторизацию...")
    login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    print(f"Статус код: {login_resp.status_code}")
    print(f"Полный ответ: {login_resp.text}")  
    
    try:
        response_data = login_resp.json()
        if "access_token" not in response_data:
            print("Ошибка: в ответе отсутствует access_token")
            print("Возможные причины:")
            print("- Неверные учетные данные")
            print("- Проблемы в работе сервера")
            print("- Неправильный формат ответа API")
            return
        
        token = response_data["access_token"]
        print(f"Успешно получили токен: {token[:15]}...")  
        
    except ValueError as e:
        print(f"Ошибка декодирования JSON: {e}")
        return

    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\nСоздаем игровую сессию...")
    session_resp = requests.post(
        f"{BASE_URL}/gamesessions/",
        json={"max_players": 4},
        headers=headers
    )
    
    print(f"Статус код: {session_resp.status_code}")
    print(f"Ответ: {session_resp.text}")

if __name__ == "__main__":
    test_api()