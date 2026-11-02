"""Generate a cryptographically secure dashboard access key."""
import secrets
print(secrets.token_urlsafe(36))
