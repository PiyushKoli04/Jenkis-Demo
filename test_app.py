import os
import json
import pytest
from app import app, init_db

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_expenses.db"
    monkeypatch.setenv("DB_PATH", str(test_db))
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        yield client

def test_home_page_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Expense Tracker" in response.data

def test_add_expense_api_returns_201(client):
    payload = {
        "title": "Coffee",
        "amount": 4.50,
        "category": "Food",
        "date": "2026-03-30"
    }
    response = client.post('/api/expenses', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] is not None
    assert data["title"] == "Coffee"
    assert data["amount"] == 4.50
    assert data["category"] == "Food"
    assert data["date"] == "2026-03-30"

def test_list_expenses_returns_added_item(client):
    payload = {
        "title": "Book",
        "amount": 25.00,
        "category": "Education",
        "date": "2026-03-29"
    }
    add_resp = client.post('/api/expenses', json=payload)
    assert add_resp.status_code == 201

    list_resp = client.get('/api/expenses')
    assert list_resp.status_code == 200
    data = list_resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    titles = [item["title"] for item in data]
    assert "Book" in titles

def test_get_one_expense(client):
    payload = {
        "title": "Train Ticket",
        "amount": 12.50,
        "category": "Travel",
        "date": "2026-03-28"
    }
    create_resp = client.post('/api/expenses', json=payload)
    item_id = create_resp.get_json()["id"]

    get_resp = client.get(f'/api/expenses/{item_id}')
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert data["id"] == item_id
    assert data["title"] == "Train Ticket"
    assert data["amount"] == 12.50

def test_update_expense_put(client):
    payload = {
        "title": "Lunch",
        "amount": 10.00,
        "category": "Food",
        "date": "2026-03-27"
    }
    create_resp = client.post('/api/expenses', json=payload)
    item_id = create_resp.get_json()["id"]

    updated_payload = {
        "title": "Team Lunch",
        "amount": 35.00,
        "category": "Food & Dining",
        "date": "2026-03-27"
    }
    put_resp = client.put(f'/api/expenses/{item_id}', json=updated_payload)
    assert put_resp.status_code == 200
    data = put_resp.get_json()
    assert data["title"] == "Team Lunch"
    assert data["amount"] == 35.00
    assert data["category"] == "Food & Dining"

def test_delete_expense(client):
    payload = {
        "title": "Temporary Item",
        "amount": 5.00,
        "category": "Misc",
        "date": "2026-03-26"
    }
    create_resp = client.post('/api/expenses', json=payload)
    item_id = create_resp.get_json()["id"]

    del_resp = client.delete(f'/api/expenses/{item_id}')
    assert del_resp.status_code == 200

    get_resp = client.get(f'/api/expenses/{item_id}')
    assert get_resp.status_code == 404

def test_get_nonexistent_returns_404(client):
    response = client.get('/api/expenses/999999')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data

def test_post_missing_fields_returns_400(client):
    incomplete_payload = {
        "title": "Incomplete Expense"
        # missing amount, category, date
    }
    response = client.post('/api/expenses', json=incomplete_payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_health_returns_200(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_metrics_returns_200_and_contains_metric(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "flask_http_request_total" in content
