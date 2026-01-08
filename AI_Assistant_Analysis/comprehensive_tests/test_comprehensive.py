"""
Комплексные интеграционные тесты для проверки корректности API
Проверка: валидация данных, обработка ошибок, бизнес-логика
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import RideModel, UserModel, ParticipationModel
from app.security import get_password_hash


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Тесты для полного цикла аутентификации"""

    async def test_complete_auth_flow(self, test_client: AsyncClient, session: AsyncSession):
        """Проверяем полный цикл: регистрация → логин → получение профиля"""
        # Регистрация
        register_payload = {"username": "newuser", "password": "newpassword"}
        register_response = await test_client.post("/users/", json=register_payload)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]

        # Логин
        login_payload = {
            "username": "newuser",
            "password": "newpassword",
        }
        login_response = await test_client.post("/auth/login", data=login_payload)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Получение профиля
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await test_client.get("/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["id"] == user_id
        assert me_response.json()["username"] == "newuser"

    async def test_auth_with_wrong_password(self, test_client: AsyncClient, test_user: UserModel):
        """Проверяем что неправильный пароль не проходит"""
        login_payload = {
            "username": test_user.username,
            "password": "wrongpassword",
        }
        response = await test_client.post("/auth/login", data=login_payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid username or password" in response.json()["detail"]

    async def test_auth_with_nonexistent_user(self, test_client: AsyncClient):
        """Проверяем что несуществующий пользователь не может войти"""
        login_payload = {
            "username": "nonexistent",
            "password": "password",
        }
        response = await test_client.post("/auth/login", data=login_payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestRideManagement:
    """Тесты для управления поездками"""

    async def test_create_ride_requires_auth(self, test_client: AsyncClient):
        """Проверяем что создание поездки требует аутентификацию"""
        payload = {
            "title": "Test Ride",
            "description": "Test",
            "start_time": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        response = await test_client.post("/rides/", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_ride_code_uniqueness(self, test_client: AsyncClient, auth_headers: dict, session: AsyncSession):
        """Проверяем что коды поездок уникальны"""
        payload = {
            "title": "Ride 1",
            "description": "Description 1",
            "start_time": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        
        response1 = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response1.status_code == status.HTTP_201_CREATED
        code1 = response1.json()["code"]
        
        response2 = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response2.status_code == status.HTTP_201_CREATED
        code2 = response2.json()["code"]
        
        # Коды должны быть разными
        assert code1 != code2

    async def test_delete_ride_authorization(self, test_client: AsyncClient, test_ride: RideModel, auth_headers: dict):
        """Проверяем что удалить поездку может только создатель"""
        another_user_header = {"Authorization": "Bearer invalid_token"}
        
        # Note: In a real scenario we'd create a second user. 
        # Here we test with invalid token which should return 401.
        # Ideally we test 403 Forbidden with a valid but non-owner user.
        
        response = await test_client.delete(f"/rides/{test_ride.id}", headers=another_user_header)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestParticipationManagement:
    """Тесты для управления участиями"""

    async def test_participation_requires_valid_ride_code(self, test_client: AsyncClient, auth_headers: dict):
        """Проверяем что участие требует существующий код поездки"""
        payload = {"ride_code": "INVALID"}
        
        response = await test_client.post("/participations/", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_participation_with_all_fields(self, test_client: AsyncClient, test_ride: RideModel, auth_headers: dict):
        """Проверяем создание участия со всеми полями"""
        # Create participation with only ride_code
        create_payload = {"ride_code": test_ride.code}
        create_response = await test_client.post("/participations/", json=create_payload, headers=auth_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        participation_id = create_response.json()["id"]
        
        # Update with coordinates and location_timestamp
        update_payload = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "location_timestamp": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        update_response = await test_client.put(f"/participations/{participation_id}", json=update_payload, headers=auth_headers)
        assert update_response.status_code == status.HTTP_200_OK
        
        data = update_response.json()
        assert data["latitude"] == 40.7128
        assert data["longitude"] == -74.0060
        assert data["updated_at"] is not None
        assert data["location_timestamp"] is not None

    async def test_participation_without_coordinates(self, test_client: AsyncClient, test_ride: RideModel, auth_headers: dict):
        """Проверяем что можно создать участие без координат"""
        payload = {"ride_code": test_ride.code}
        
        response = await test_client.post("/participations/", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["latitude"] is None
        assert data["longitude"] is None
        # updated_at is auto-generated by database
        assert data["updated_at"] is not None
        assert data["location_timestamp"] is None

    async def test_get_all_participations(self, test_client: AsyncClient, session: AsyncSession, test_user: UserModel, auth_headers: dict):
        """Проверяем получение списка всех участий"""
        # Создаем несколько поездок и участий (UNIQUE constraint требует разные ride_id)
        from app.models import RideModel
        for i in range(3):
            ride = RideModel(
                code=f"TESTRIDE{i}",
                title=f"Test Ride {i}",
                description="Test",
                start_time=datetime(2025, 11, 20 + i, 10, 0, tzinfo=timezone.utc),
                created_by_user_id=test_user.id,
            )
            session.add(ride)
            await session.flush()
            
            participation = ParticipationModel(
                user_id=test_user.id,
                ride_id=ride.id,
                latitude=40.0 + i,
                longitude=-74.0 + i,
            )
            session.add(participation)
        await session.commit()
        
        response = await test_client.get("/participations/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3


@pytest.mark.asyncio
class TestDataValidation:
    """Тесты для валидации данных"""

    async def test_invalid_datetime_format(self, test_client: AsyncClient, auth_headers: dict):
        """Проверяем что неправильный формат даты отклоняется"""
        payload = {
            "title": "Test",
            "description": "Test",
            "start_time": "invalid-date",
        }
        response = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_missing_required_fields(self, test_client: AsyncClient, auth_headers: dict):
        """Проверяем что отсутствие обязательных полей вызывает ошибку"""
        payload = {"title": "Test"}  # Отсутствует start_time
        response = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_invalid_coordinate_ranges(self, test_client: AsyncClient, test_ride: RideModel, auth_headers: dict):
        """Проверяем что экстремальные координаты принимаются"""
        # Create participation first
        create_payload = {"ride_code": test_ride.code}
        create_response = await test_client.post("/participations/", json=create_payload, headers=auth_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        participation_id = create_response.json()["id"]
        
        # Update with extreme coordinates
        update_payload = {
            "latitude": 90.0,
            "longitude": 180.0,
            "location_timestamp": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        response = await test_client.put(f"/participations/{participation_id}", json=update_payload, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestEdgeCases:
    """Тесты для граничных случаев"""

    async def test_empty_ride_list(self, test_client: AsyncClient):
        """Проверяем что пустой список поездок возвращает пустой массив"""
        response = await test_client.get("/rides/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_ride_with_special_characters_in_title(self, test_client: AsyncClient, auth_headers: dict):
        """Проверяем что специальные символы в названии работают"""
        payload = {
            "title": "Test Ride & Special Chars \"'!@#$%",
            "description": "Test",
            "start_time": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        response = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        assert "Special" in response.json()["title"]

    async def test_very_long_title(self, test_client: AsyncClient, auth_headers: dict):
        """Проверяем что очень длинное название обрабатывается"""
        long_title = "A" * 100
        payload = {
            "title": long_title,
            "description": "Test",
            "start_time": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        response = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_CONTENT]

    async def test_null_description(self, test_client: AsyncClient, auth_headers: dict):
        """Проверяем что null description работает"""
        payload = {
            "title": "Test Ride",
            "description": None,
            "start_time": datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
        }
        response = await test_client.post("/rides/", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["description"] is None


@pytest.mark.asyncio
class TestSecurityAndAuthorization:
    """Тесты для проверки безопасности"""

    async def test_invalid_token_format(self, test_client: AsyncClient):
        """Проверяем что неправильный формат токена отклоняется"""
        headers = {"Authorization": "Bearer invalid.token.format"}
        response = await test_client.get("/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_bearer_prefix(self, test_client: AsyncClient):
        """Проверяем что токен без Bearer префикса не работает"""
        headers = {"Authorization": "some_token_without_bearer"}
        response = await test_client.get("/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_authorization_header(self, test_client: AsyncClient):
        """Проверяем что отсутствие заголовка Authorization вызывает 401"""
        response = await test_client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_expired_or_invalid_jwt(self, test_client: AsyncClient):
        """Проверяем что невалидный JWT отклоняется"""
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"}
        response = await test_client.get("/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestResponseFormats:
    """Тесты для проверки формата ответов"""

    async def test_ride_response_includes_all_fields(self, test_client: AsyncClient, test_ride):
        """Проверяем что ответ поездки содержит все необходимые поля"""
        response = await test_client.get(f"/rides/{test_ride.id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        required_fields = ["id", "code", "title", "description", "start_time", "created_by_user_id", "created_at", "is_active"]
        for field in required_fields:
            assert field in data, f"Field {field} missing from ride response"

    async def test_participation_response_includes_all_fields(self, test_client: AsyncClient, test_participation):
        """Проверяем что ответ участия содержит все необходимые поля"""
        response = await test_client.get(f"/participations/{test_participation.id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        required_fields = ["id", "user_id", "ride_id", "latitude", "longitude", "updated_at", "location_timestamp"]
        for field in required_fields:
            assert field in data, f"Field {field} missing from participation response"

    async def test_list_responses_are_arrays(self, test_client: AsyncClient):
        """Проверяем что список ответы возвращают массивы"""
        responses_data = [
            ("/rides/", "Rides"),
            ("/participations/", "Participations"),
            # ("/users/", "Users"), # user list might be restricted
        ]
        
        for url, name in responses_data:
            response = await test_client.get(url)
            assert response.status_code == status.HTTP_200_OK, f"{name} list failed"
            assert isinstance(response.json(), list), f"{name} response is not a list"

    async def test_datetime_format_consistency(self, test_client: AsyncClient, test_ride):
        """Проверяем что формат datetime консистентен"""
        response = await test_client.get(f"/rides/{test_ride.id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Проверяем что даты в формате ISO
        assert "T" in data["start_time"]
        assert "T" in data["created_at"]


@pytest.mark.asyncio
class TestConcurrency:
    """Тесты для проверки обработки одновременных операций"""

    async def test_multiple_participations_same_ride(self, test_client: AsyncClient, test_ride, session):
        """Проверяем что несколько пользователей могут участвовать в одной поездке"""
        from app.models import UserModel
        
        # Создаем нескольких пользователей
        for i in range(3):
            hashed_password = get_password_hash("password")
            user = UserModel(username=f"participant{i}", password=hashed_password)
            session.add(user)
            await session.commit()
            
            # Логиним и создаем участие
            login_response = await test_client.post(
                "/auth/login",
                data={"username": f"participant{i}", "password": "password"},
            )
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            payload = {"ride_code": test_ride.code}
            response = await test_client.post("/participations/", json=payload, headers=headers)
            assert response.status_code == status.HTTP_201_CREATED
        
        # Проверяем что все участия созданы
        all_participations = await test_client.get("/participations/")
        assert len(all_participations.json()) >= 3
