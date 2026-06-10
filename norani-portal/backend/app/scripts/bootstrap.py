"""Bootstrap the database with initial data.

Run after `alembic upgrade head`. Creates:
  - An internal Norani CustomerAccount (the admin/staff account)
  - A first admin user
  - A catalog of common device types (Dragino, Milesight, etc.)

Usage:
    python -m app.scripts.bootstrap
"""

import asyncio
import os
import sys
import uuid
from getpass import getpass
from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.db.models.customer_account import CustomerAccount
from app.db.models.device_type import DeviceType
from app.db.models.user import User
from app.services.chirpstack_client import cs_client, ChirpStackError

settings = get_settings()


# Catalog of device types to seed. The chirpstack_profile_id is a placeholder
# that you replace with real UUIDs after creating profiles in ChirpStack.
SEED_DEVICE_TYPES = [
    {
        "name": "Dragino LHT65N — Temperature + Humidity",
        "manufacturer": "Dragino",
        "model": "LHT65N",
        "region": "eu868",
        "description": "Battery-powered indoor temp & humidity sensor with ~5 year battery life",
        "icon": "thermometer",
    },
    {
        "name": "Milesight EM300-TH — Temp + Humidity (IP67)",
        "manufacturer": "Milesight",
        "model": "EM300-TH",
        "region": "eu868",
        "description": "Outdoor-rated environmental sensor",
        "icon": "thermometer",
    },
    {
        "name": "Dragino SE01 — Soil Moisture",
        "manufacturer": "Dragino",
        "model": "SE01-LB",
        "region": "eu868",
        "description": "Soil moisture + temperature sensor for agriculture",
        "icon": "leaf",
    },
    {
        "name": "Milesight EM500-UDL — Ultrasonic Distance/Level",
        "manufacturer": "Milesight",
        "model": "EM500-UDL",
        "region": "eu868",
        "description": "Tank level / water height monitoring",
        "icon": "water",
    },
    {
        "name": "Generic Water Meter (LoRaWAN AMR)",
        "manufacturer": "Generic",
        "model": "AMR-868",
        "region": "eu868",
        "description": "Smart water meter for WASAC-style deployments",
        "icon": "droplet",
    },
]


async def bootstrap():
    print("=" * 60)
    print("Norani Portal — Bootstrap")
    print("=" * 60)

    # Collect admin user info
    print("\nCreate the first admin user (Norani internal staff):\n")

    admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL") or input("Admin email: ").strip().lower()
    admin_name = os.getenv("BOOTSTRAP_ADMIN_NAME") or input("Admin full name: ").strip()
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    if not admin_password:
        admin_password = getpass("Admin password (>= 8 chars): ")
        if len(admin_password) < 8:
            print("ERROR: Password must be at least 8 characters")
            sys.exit(1)

    norani_account_name = os.getenv("BOOTSTRAP_ACCOUNT_NAME", "Norani Internal")

    async with AsyncSessionLocal() as db:
        # Check if already bootstrapped
        existing = await db.execute(select(User).where(User.email == admin_email))
        if existing.scalar_one_or_none():
            print(f"\nUser {admin_email} already exists. Aborting.")
            sys.exit(1)

        # 1. Create ChirpStack tenant for Norani (the internal account)
        print(f"\n[1/4] Creating ChirpStack tenant '{norani_account_name}'...")
        try:
            tenant_id = cs_client.create_tenant(
                name=norani_account_name,
                can_have_gateways=True,  # Norani owns the gateways
            )
            app_id = cs_client.create_application(
                tenant_id=tenant_id,
                name="Norani Default Application",
            )
            print(f"   ✓ ChirpStack tenant: {tenant_id}")
            print(f"   ✓ ChirpStack application: {app_id}")
        except ChirpStackError as e:
            print(f"   ✗ FAILED: {e}")
            print("\nMake sure ChirpStack is running and CHIRPSTACK_API_TOKEN is set in .env")
            sys.exit(1)

        # 2. Create customer account
        print(f"\n[2/4] Creating CustomerAccount...")
        account = CustomerAccount(
            name=norani_account_name,
            contact_email=admin_email,
            chirpstack_tenant_id=tenant_id,
            chirpstack_application_id=app_id,
            plan_tier="internal",
            price_per_device_rwf=0,  # Internal account is free
        )
        db.add(account)
        await db.flush()
        print(f"   ✓ CustomerAccount id: {account.id}")

        # 3. Create admin user
        print(f"\n[3/4] Creating admin user...")
        user = User(
            customer_account_id=account.id,
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name=admin_name,
            role="admin",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        print(f"   ✓ User id: {user.id}")

        # 4. Seed device types
        print(f"\n[4/4] Seeding device type catalog...")
        for dt in SEED_DEVICE_TYPES:
            device_type = DeviceType(
                name=dt["name"],
                manufacturer=dt["manufacturer"],
                model=dt["model"],
                # Placeholder — replace after creating profile in ChirpStack
                chirpstack_profile_id=str(uuid.uuid4()),
                region=dt["region"],
                description=dt["description"],
                icon=dt["icon"],
            )
            db.add(device_type)
            print(f"   ✓ {dt['name']}")

        await db.commit()

    print("\n" + "=" * 60)
    print("Bootstrap complete!")
    print("=" * 60)
    print(f"\nLogin at https://portal.norani.rw with:")
    print(f"  email: {admin_email}")
    print(f"  password: (the one you entered)")
    print("\nNext steps:")
    print("  1. Create Device Profiles in ChirpStack web UI for each device model")
    print("  2. Update the chirpstack_profile_id values in the device_types table")
    print("     to match the real ChirpStack profile UUIDs")
    print("  3. Provision your first customer account via /api/v1/admin/customers")
    print()


if __name__ == "__main__":
    asyncio.run(bootstrap())
