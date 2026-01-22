from app.auth.session import RoleChecker
from app.models.users import Role

allow_root = RoleChecker([Role.ROOT])
allow_admin = RoleChecker([Role.ROOT, Role.ADMIN])
allow_teacher = RoleChecker([Role.ROOT, Role.ADMIN, Role.TEACHER])
allow_student = RoleChecker([Role.ROOT, Role.ADMIN, Role.STUDENT])
allow_authorized = RoleChecker([Role.ROOT, Role.ADMIN, Role.TEACHER, Role.STUDENT])

__all__ = [
    "allow_root",
    "allow_admin",
    "allow_teacher",
    "allow_student",
    "allow_authorized",
]
