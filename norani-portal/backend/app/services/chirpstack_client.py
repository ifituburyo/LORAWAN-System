"""ChirpStack gRPC API client.

Encapsulates all gRPC complexity behind a clean Python interface. Used by the
device-management endpoints to provision tenants, applications, and devices.
"""

import logging
from typing import Optional
import grpc
from chirpstack_api import api

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ChirpStackError(Exception):
    """Raised when a ChirpStack gRPC call fails."""
    pass


class ChirpStackClient:
    """Singleton wrapper over ChirpStack's gRPC API."""

    def __init__(self) -> None:
        self.channel = grpc.insecure_channel(settings.chirpstack_api_url)
        self.auth_metadata = [
            ("authorization", f"Bearer {settings.chirpstack_api_token}")
        ]
        self.tenant_stub = api.TenantServiceStub(self.channel)
        self.application_stub = api.ApplicationServiceStub(self.channel)
        self.device_stub = api.DeviceServiceStub(self.channel)
        self.device_profile_stub = api.DeviceProfileServiceStub(self.channel)

    # ============ Tenants ============

    def create_tenant(
        self,
        name: str,
        max_device_count: int = 10000,
        max_gateway_count: int = 50,
        can_have_gateways: bool = False,
    ) -> str:
        """Create a ChirpStack tenant. Returns the tenant ID (UUID string)."""
        try:
            req = api.CreateTenantRequest(
                tenant=api.Tenant(
                    name=name,
                    max_device_count=max_device_count,
                    max_gateway_count=max_gateway_count,
                    can_have_gateways=can_have_gateways,
                    private_gateways_up=False,
                    private_gateways_down=False,
                )
            )
            resp = self.tenant_stub.Create(req, metadata=self.auth_metadata)
            logger.info("Created ChirpStack tenant: %s (%s)", name, resp.id)
            return resp.id
        except grpc.RpcError as e:
            logger.error("Failed to create tenant %s: %s", name, e.details())
            raise ChirpStackError(f"Failed to create tenant: {e.details()}")

    def delete_tenant(self, tenant_id: str) -> None:
        """Delete a tenant. Used to roll back failed account provisioning."""
        try:
            req = api.DeleteTenantRequest(id=tenant_id)
            self.tenant_stub.Delete(req, metadata=self.auth_metadata)
            logger.info("Deleted ChirpStack tenant: %s", tenant_id)
        except grpc.RpcError as e:
            logger.warning("Failed to delete tenant %s: %s", tenant_id, e.details())

    # ============ Applications ============

    def create_application(
        self,
        tenant_id: str,
        name: str = "Default",
        description: str = "Default application created by Norani Portal",
    ) -> str:
        """Create an application under a tenant. Returns the application ID."""
        try:
            req = api.CreateApplicationRequest(
                application=api.Application(
                    name=name,
                    description=description,
                    tenant_id=tenant_id,
                )
            )
            resp = self.application_stub.Create(req, metadata=self.auth_metadata)
            logger.info("Created ChirpStack application: %s (%s)", name, resp.id)
            return resp.id
        except grpc.RpcError as e:
            logger.error("Failed to create application: %s", e.details())
            raise ChirpStackError(f"Failed to create application: {e.details()}")

    # ============ Devices ============

    def create_device(
        self,
        dev_eui: str,
        join_eui: str,
        app_key: str,
        application_id: str,
        device_profile_id: str,
        name: str,
        description: str = "",
    ) -> None:
        """
        Create a device in ChirpStack and set its OTAA keys.

        This is two gRPC calls — create the device, then set its keys.
        Both must succeed for the device to be usable.
        """
        # 1. Create the device record
        try:
            dev_req = api.CreateDeviceRequest(
                device=api.Device(
                    dev_eui=dev_eui,
                    join_eui=join_eui,
                    application_id=application_id,
                    device_profile_id=device_profile_id,
                    name=name,
                    description=description,
                    is_disabled=False,
                    skip_fcnt_check=False,
                )
            )
            self.device_stub.Create(dev_req, metadata=self.auth_metadata)
            logger.info("Created device in ChirpStack: %s", dev_eui)
        except grpc.RpcError as e:
            logger.error("Failed to create device %s: %s", dev_eui, e.details())
            raise ChirpStackError(f"Failed to create device: {e.details()}")

        # 2. Set the device keys (OTAA)
        try:
            keys_req = api.CreateDeviceKeysRequest(
                device_keys=api.DeviceKeys(
                    dev_eui=dev_eui,
                    nwk_key=app_key,  # For LoRaWAN 1.0.x, AppKey lives here
                    app_key=app_key,  # Also set this for 1.1 compatibility
                )
            )
            self.device_stub.CreateKeys(keys_req, metadata=self.auth_metadata)
            logger.info("Set keys for device: %s", dev_eui)
        except grpc.RpcError as e:
            # Roll back: delete the device we just created
            logger.error("Failed to set keys for %s: %s. Rolling back.", dev_eui, e.details())
            try:
                self.delete_device(dev_eui)
            except ChirpStackError:
                pass
            raise ChirpStackError(f"Failed to set device keys: {e.details()}")

    def delete_device(self, dev_eui: str) -> None:
        """Delete a device from ChirpStack."""
        try:
            req = api.DeleteDeviceRequest(dev_eui=dev_eui)
            self.device_stub.Delete(req, metadata=self.auth_metadata)
            logger.info("Deleted device from ChirpStack: %s", dev_eui)
        except grpc.RpcError as e:
            logger.error("Failed to delete device %s: %s", dev_eui, e.details())
            raise ChirpStackError(f"Failed to delete device: {e.details()}")

    def get_device(self, dev_eui: str) -> Optional[dict]:
        """Fetch a device's current state from ChirpStack."""
        try:
            req = api.GetDeviceRequest(dev_eui=dev_eui)
            resp = self.device_stub.Get(req, metadata=self.auth_metadata)
            return {
                "dev_eui": resp.device.dev_eui,
                "name": resp.device.name,
                "last_seen_at": resp.last_seen_at.ToDatetime() if resp.HasField("last_seen_at") else None,
                "device_status": {
                    "battery_level": resp.device_status.battery_level if resp.HasField("device_status") else None,
                    "margin": resp.device_status.margin if resp.HasField("device_status") else None,
                },
            }
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            logger.error("Failed to get device %s: %s", dev_eui, e.details())
            raise ChirpStackError(f"Failed to get device: {e.details()}")


# Module-level singleton
cs_client = ChirpStackClient()
