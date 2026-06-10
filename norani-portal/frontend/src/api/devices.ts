import { api } from "./client";
import type {
  Device,
  DeviceCreatedResponse,
  DeviceList,
  DeviceMeasurement,
  DeviceType,
} from "./types";

export interface ListDevicesParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
}

export async function listDevices(params: ListDevicesParams = {}): Promise<DeviceList> {
  const res = await api.get<DeviceList>("/devices", { params });
  return res.data;
}

export async function getDevice(devEui: string): Promise<Device> {
  const res = await api.get<Device>(`/devices/${devEui}`);
  return res.data;
}

export async function listDeviceTypes(): Promise<DeviceType[]> {
  const res = await api.get<DeviceType[]>("/devices/types");
  return res.data;
}

export interface CreateDevicePayload {
  name: string;
  device_type_id: string;
  dev_eui: string;
  join_eui?: string;
  location_name?: string;
  location_lat?: number;
  location_lon?: number;
}

export async function createDevice(payload: CreateDevicePayload): Promise<DeviceCreatedResponse> {
  const res = await api.post<DeviceCreatedResponse>("/devices", payload);
  return res.data;
}

export async function updateDevice(
  devEui: string,
  payload: Partial<{
    name: string;
    location_name: string;
    location_lat: number;
    location_lon: number;
    status: string;
  }>,
): Promise<Device> {
  const res = await api.patch<Device>(`/devices/${devEui}`, payload);
  return res.data;
}

export async function deleteDevice(devEui: string): Promise<void> {
  await api.delete(`/devices/${devEui}`);
}

export interface MeasurementParams {
  from_time?: string;
  to_time?: string;
  hours?: number;
  field?: string;
}

export async function getDeviceMeasurements(
  devEui: string,
  params: MeasurementParams = {},
): Promise<{ measurements: DeviceMeasurement[]; count: number; from: string; to: string }> {
  const res = await api.get(`/devices/${devEui}/measurements`, { params });
  return res.data;
}

export async function exportDeviceData(
  devEui: string,
  fmt: "csv" | "json" | "xlsx",
  params: MeasurementParams,
): Promise<void> {
  const res = await api.get(`/devices/${devEui}/export`, {
    params: { fmt, ...params },
    responseType: "blob",
  });
  const contentDisposition = res.headers["content-disposition"] ?? "";
  const match = contentDisposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : `${devEui}_export.${fmt}`;
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function getDeviceLatest(devEui: string): Promise<{
  latest: { timestamp: string; fields: Record<string, number> } | null;
}> {
  const res = await api.get(`/devices/${devEui}/latest`);
  return res.data;
}

/** Build the URL for fetching a device sticker PDF.
 *  Pass appKey for the immediate post-creation flow; omit to use stored key (admin only).
 */
export function getStickerUrl(devEui: string, appKey?: string): string {
  const base = `/api/v1/devices/${devEui}/sticker`;
  return appKey ? `${base}?app_key=${encodeURIComponent(appKey)}` : base;
}
