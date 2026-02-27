"""
Tests for the User model

Covers:
  • Instantiation
  • Role validation
  • Default values
  • No dependency on routes or services
"""

import uuid
import pytest
from app.models.user import User, UserRole



# Instantiation & defaults

class TestUserDefaults:
    """Verify inherited and custom default values."""

    def test_role_defaults_to_student(self):
        user = User(email="alice@example.com", hashed_password="hash")
        assert user.role == UserRole.STUDENT

    def test_is_active_defaults_to_true(self):
        user = User(email="alice@example.com", hashed_password="hash")
        assert user.is_active is True

    def test_is_superuser_defaults_to_false(self):
        user = User(email="alice@example.com", hashed_password="hash")
        assert user.is_superuser is False

    def test_is_verified_defaults_to_false(self):
        user = User(email="alice@example.com", hashed_password="hash")
        assert user.is_verified is False

    def test_id_is_uuid(self):
        user = User(email="alice@example.com", hashed_password="hash")
        assert isinstance(user.id, uuid.UUID)



# Valid role assignment

class TestUserRoleAssignment:
    """Ensure each valid role can be set via the enum or as a raw string."""

    @pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN])
    def test_create_with_enum_role(self, role: UserRole):
        user = User(email="bob@example.com", hashed_password="hash", role=role)
        assert user.role == role

    @pytest.mark.parametrize("role_str", ["student", "teacher", "admin"])
    def test_create_with_string_role_via_model_validate(self, role_str: str):
        """model_validate is the path used by FastAPI request parsing."""
        user = User.model_validate(
            {"email": "carol@example.com", "hashed_password": "hash", "role": role_str}
        )
        assert user.role == UserRole(role_str)



# Role validation — invalid values rejected

class TestUserRoleValidation:
    """
    Role validation is enforced via a Pydantic field_validator which runs
    during model_validate.
    """

    @pytest.mark.parametrize("bad_role", ["moderator", "superadmin", "", "STUDENT", "Admin"])
    def test_invalid_role_rejected_via_model_validate(self, bad_role: str):
        with pytest.raises(Exception):  # ValidationError
            User.model_validate(
                {"email": "bad@example.com", "hashed_password": "hash", "role": bad_role}
            )



# UserRole enum integrity

class TestUserRoleEnum:
    """Confirm the enum has exactly three members with the expected values."""

    def test_enum_members(self):
        assert set(UserRole) == {UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN}

    def test_enum_values(self):
        assert UserRole.STUDENT.value == "student"
        assert UserRole.TEACHER.value == "teacher"
        assert UserRole.ADMIN.value == "admin"

    def test_enum_is_str_subclass(self):
        """The enum values should be usable as plain strings."""
        assert isinstance(UserRole.STUDENT, str)