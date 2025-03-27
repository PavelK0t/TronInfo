import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, Base, get_db, RequestLog

# Создание тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db  # Передача сессии тесту
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_post_address_info(client, db_session):
    """
    Проверяет, что API возвращает корректные данные при запросе к /address-info/
    """
    response = client.post("/address-info/", json={"address": "TXaY7P8snhMi5sHQaFjJw3nX5sA2t6PzqJ"})
    assert response.status_code == 200  # Ожидаем успешный ответ
    data = response.json()
    assert "balance" in data  # Проверяем, что в ответе есть баланс
    assert "bandwidth" in data  # Проверяем, что в ответе есть bandwidth
    assert "energy" in data  # Проверяем, что в ответе есть energy


def test_get_requests(client, db_session):
    """
    Проверяет, что при запросе к /requests/ API возвращает записи из базы данных
    """
    # Добавляем тестовую запись в БД
    db_session.add(RequestLog(address="TX123", balance=100, bandwidth=500, energy=300))
    db_session.commit()

    response = client.get("/requests/")
    assert response.status_code == 200  # Проверяем успешный статус-код
    data = response.json()
    assert len(data["requests"]) > 0  # Проверяем, что запросы в БД есть
