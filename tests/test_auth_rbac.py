from app.core.security import hash_password
from app.models.user import User, UserRole


def create_user(
    db,
    email,
    role,
    password="TestPassword123!",
):
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login(client, email, password="TestPassword123!"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_register_and_login(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "Student",
        },
    )

    assert response.status_code == 201

    token = login(
        client,
        "student@example.com",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_student_rbac(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "Student",
        },
    )

    token = login(
        client,
        "student@example.com",
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    assert client.get(
        "/api/v1/auth/student-test",
        headers=headers,
    ).status_code == 200

    assert client.get(
        "/api/v1/auth/teacher-test",
        headers=headers,
    ).status_code == 403

    assert client.get(
        "/api/v1/auth/admin-test",
        headers=headers,
    ).status_code == 403


def test_teacher_rbac(client, db):
    teacher = create_user(
        db,
        "teacher@test.com",
        UserRole.TEACHER,
    )

    token = login(
        client,
        teacher.email,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    assert client.get(
        "/api/v1/auth/teacher-test",
        headers=headers,
    ).status_code == 200

    assert client.get(
        "/api/v1/auth/student-test",
        headers=headers,
    ).status_code == 403

    assert client.get(
        "/api/v1/auth/admin-test",
        headers=headers,
    ).status_code == 403


def test_admin_rbac(client, db):
    admin = create_user(
        db,
        "admin@test.com",
        UserRole.ADMIN,
    )

    token = login(
        client,
        admin.email,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    assert client.get(
        "/api/v1/auth/admin-test",
        headers=headers,
    ).status_code == 200

    assert client.get(
        "/api/v1/auth/student-test",
        headers=headers,
    ).status_code == 403

    assert client.get(
        "/api/v1/auth/teacher-test",
        headers=headers,
    ).status_code == 403


def test_admin_cannot_demote_themselves(client, db):
    admin = create_user(
        db,
        "admin@test.com",
        UserRole.ADMIN,
    )

    token = login(
        client,
        admin.email,
    )

    response = client.patch(
        f"/api/v1/admin/users/{admin.id}/role",
        json={
            "role": "student",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400


def test_admin_can_deactivate_user(client, db):
    admin = create_user(
        db,
        "admin@test.com",
        UserRole.ADMIN,
    )

    student = create_user(
        db,
        "student@test.com",
        UserRole.STUDENT,
    )

    admin_token = login(
        client,
        admin.email,
    )

    student_token = login(
        client,
        student.email,
    )

    response = client.patch(
        f"/api/v1/admin/users/{student.id}/status",
        json={
            "is_active": False,
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {student_token}",
        },
    )

    assert response.status_code == 403


def test_refresh_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "Student",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    refresh_token = response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()