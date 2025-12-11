# Integration Tests

Интеграционные тесты для SafeRide API, которые работают с реальной базой данных.

## Описание

Эти тесты проверяют работу всех endpoints API с реальной SQLite базой данных (не используют моки или фейковые данные).

## Структура

- `conftest.py` - Конфигурация тестов, fixtures для базы данных и аутентификации
- `test_users_integration.py` - Тесты для endpoints пользователей
- `test_auth_integration.py` - Тесты для endpoints аутентификации
- `test_rides_integration.py` - Тесты для endpoints поездок
- `test_participations_integration.py` - Тесты для endpoints участия в поездках

## Что тестируется

### Users
- ✅ Создание пользователя
- ✅ Проверка дубликатов username
- ✅ Получение пользователя по ID
- ✅ Получение всех пользователей
- ✅ Обработка несуществующих пользователей

### Authentication
- ✅ Успешный логин
- ✅ Неправильный пароль
- ✅ Несуществующий пользователь
- ✅ Получение текущего пользователя
- ✅ Проверка токенов

### Rides
- ✅ Создание поездки
- ✅ Получение всех поездок
- ✅ Получение поездки по ID
- ✅ Получение поездки по коду
- ✅ Обновление поездки владельцем
- ✅ Запрет обновления чужой поездки
- ✅ Удаление поездки владельцем
- ✅ Запрет удаления чужой поездки
- ✅ Проверка авторизации

### Participations
- ✅ Создание участия (присоединение к поездке)
- ✅ Получение всех участий
- ✅ Получение участия по ID
- ✅ Обновление статуса участия
- ✅ Несколько пользователей в одной поездке
- ✅ Проверка авторизации

## Запуск тестов

### Запуск всех интеграционных тестов:
```powershell
pytest integration_tests/
```

### Запуск конкретного файла тестов:
```powershell
pytest integration_tests/test_users_integration.py
```

### Запуск с подробным выводом:
```powershell
pytest integration_tests/ -v
```

### Запуск с выводом print statements:
```powershell
pytest integration_tests/ -s
```

### Запуск конкретного теста:
```powershell
pytest integration_tests/test_rides_integration.py::TestRideEndpoints::test_create_ride -v
```

## Особенности

1. **Реальная база данных**: Используется отдельная SQLite БД `test_integration.db`
2. **Изоляция тестов**: Каждый тест работает с чистой базой данных
3. **Автоматическая очистка**: БД очищается после каждого теста
4. **Настоящая аутентификация**: Используются реальные JWT токены
5. **Полная интеграция**: Тестируется весь стек от API до базы данных

## Fixtures

- `test_engine` - SQLAlchemy engine для тестовой БД (scope: session)
- `test_db` - Сессия БД для каждого теста (scope: function)
- `client` - TestClient для HTTP запросов (scope: function)
- `auth_headers` - Headers с JWT токеном для первого тестового пользователя
- `second_user_headers` - Headers с JWT токеном для второго тестового пользователя

## Требования

Все зависимости уже установлены из `requirements.txt`:
- pytest
- fastapi
- sqlalchemy
- httpx (для TestClient)
