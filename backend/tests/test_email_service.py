import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_service import EmailService


@pytest.fixture
def svc():
    return EmailService()


def test_password_reset_template_uses_reset_confirm_route(svc: EmailService):
    subject, html_content, text_content = svc.get_password_reset_email(
        name="Alice",
        token="token123",
        app_url="https://example.com",
    )

    assert "Reset Your Password" in subject
    assert "https://example.com/reset?token=token123" in html_content
    assert "https://example.com/reset?token=token123" in text_content


def test_verification_template_contains_code_and_token(svc: EmailService):
    subject, html_content, text_content = svc.get_verification_email(
        name="Alice",
        code="123456",
        token="abc123",
        app_url="https://example.com",
    )

    assert "Verify" in subject
    assert "123456" in html_content
    assert "abc123" in html_content
    assert "123456" in text_content


@pytest.mark.asyncio
async def test_mock_send_returns_success(svc: EmailService):
    # call underlying mock sender directly so this remains deterministic
    result = await svc._send_mock("user@example.com", "Test Subject")
    assert result is True
