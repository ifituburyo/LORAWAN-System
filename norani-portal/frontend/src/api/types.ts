// Shared types — must stay in sync with backend Pydantic schemas

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: "admin" | "operator" | "viewer";
  customer_account_id: string;
  customer_account_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface DeviceType {
  id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  region: string;
  description: string | null;
}

export interface Device {
  id: string;
  dev_eui: string;
  join_eui: string;
  name: string;
  location_name: string | null;
  location_lat: number | null;
  location_lon: number | null;
  status: "pending" | "active" | "offline" | "disabled";
  last_seen_at: string | null;
  created_at: string;
  device_type: DeviceType;
}

export interface DeviceCreatedResponse extends Device {
  app_key: string; // returned ONCE at creation
  sticker_url: string;
}

export interface DeviceList {
  items: Device[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeviceMeasurement {
  timestamp: string;
  field: string;
  value: number;
}

export interface CurrentBilling {
  device_count: number;
  period_start: string;
  period_end: string;
  amount_rwf: number;
  amount_usd: number;
  price_per_device_rwf: number;
}

export interface CustomerAccount {
  id: string;
  name: string;
  contact_email: string;
  phone: string | null;
  address: string | null;
  plan_tier: string;
  price_per_device_rwf: number;
  is_active: boolean;
  created_at: string;
}
