import smtplib
import ssl
import time

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from system.checks import BaseCheck, CheckResult
from system.registries import dependency_registry


class EmailSettings(BaseSettings):
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: SecretStr = SecretStr("")
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Example"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_USE_CREDENTIALS: bool = True


@dependency_registry.register()
class EmailTest(BaseCheck):
    """Test email server connectivity."""

    name = "email"

    async def test(self) -> CheckResult:
        """Test email server connection."""
        from core.config import settings

        start_time = time.time()

        # Test SMTP connection
        server: smtplib.SMTP | smtplib.SMTP_SSL
        if settings.MAIL_SSL:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT, context=context)
        else:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
            if settings.MAIL_TLS:
                context = ssl.create_default_context()
                server.starttls(context=context)

        if settings.MAIL_USE_CREDENTIALS:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD.get_secret_value())

        server.quit()

        duration_ms = (time.time() - start_time) * 1000

        return CheckResult(
            name=self.name,
            status="success",
            message="Email server connection successful",
            details={
                "server": settings.MAIL_SERVER,
                "port": settings.MAIL_PORT,
                "tls": settings.MAIL_TLS,
                "ssl": settings.MAIL_SSL,
                "authenticated": settings.MAIL_USE_CREDENTIALS,
            },
            duration_ms=duration_ms,
        )
