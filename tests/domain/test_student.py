# uv run -m pytest tests/domain/test_student.py

import pytest

from domain.student import Student, StudentStatus, RoleEnum

pytestmark = pytest.mark.unit


def test_register_valid_student_should_return_registered_student():
    # Arrange
    line_user_id = "U123"
    student_id = "s456"
    mdl_id = "m789"
    name = "小明"
    context_title = "AI課程"
    role = RoleEnum.STUDENT
    is_active = True

    # Act
    student = Student.register(
        line_user_id=line_user_id,
        student_id=student_id,
        mdl_id=mdl_id,
        name=name,
        context_title=context_title,
        role=role,
        is_active=is_active
    )

    # Assert
    assert student.line_user_id == line_user_id
    assert student.student_id == student_id
    assert student.name == name
    assert student.status == StudentStatus.REGISTERED
    assert student.role == RoleEnum.STUDENT
    assert student.is_registered()


def test_register_should_raise_when_missing_student_id():
    # Arrange
    with pytest.raises(ValueError, match="Student ID and Line User ID cannot be empty."):
        Student.register(
            line_user_id="U123",
            student_id="",  # 缺 student_id
            mdl_id="m789",
            name="小明",
            context_title="AI課程",
            role=RoleEnum.STUDENT,
            is_active=True
        )


def test_register_should_raise_when_missing_line_user_id():
    # Arrange
    with pytest.raises(ValueError, match="Student ID and Line User ID cannot be empty."):
        Student.register(
            line_user_id="",  # 缺 line_user_id
            student_id="s456",
            mdl_id="m789",
            name="小明",
            context_title="AI課程",
            role=RoleEnum.STUDENT,
            is_active=True
        )


def test_is_registered_should_return_true():
    # Arrange
    student = Student(
        line_user_id="U123",
        student_id="s456",
        mdl_id="m789",
        name="小明",
        context_title="AI課程",
        role=RoleEnum.STUDENT,
        is_active=True,
        status=StudentStatus.REGISTERED
    )

    # Act & Assert
    assert student.is_registered() is True
