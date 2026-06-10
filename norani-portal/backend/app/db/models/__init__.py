"""Import all models so Alembic autogenerate can discover them."""

from app.db.models.customer_account import CustomerAccount  # noqa
from app.db.models.user import User  # noqa
from app.db.models.device_type import DeviceType  # noqa
from app.db.models.device import Device  # noqa
from app.db.models.invoice import Invoice  # noqa
from app.db.models.audit import AuditLog  # noqa
