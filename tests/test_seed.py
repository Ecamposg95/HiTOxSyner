from sqlalchemy import func, select

from app.models.action import Action
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.user import User
from app.seed import seed


def test_seed_is_idempotent_and_creates_demo_data(db, client):
    seed(db)
    seed(db)
    assert db.scalar(select(func.count()).select_from(User)) == 3
    assert db.scalar(select(func.count()).select_from(Finding)) == 5
    assert db.scalar(select(func.count()).select_from(Initiative)) == 4
    assert db.scalar(select(func.count()).select_from(Action)) == 8
    titles = list(db.scalars(select(Finding.title)))
    assert all(t.startswith("[Demo]") for t in titles)
    response = client.post("/api/auth/login", json={"email": "admin@syner.demo", "password": "syner-demo"})
    assert response.status_code == 200
