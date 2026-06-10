import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import DeviceList from "./pages/DeviceList";
import AddDevice from "./pages/AddDevice";
import DeviceDetail from "./pages/DeviceDetail";
import StickerView from "./pages/StickerView";
import Billing from "./pages/Billing";
import Account from "./pages/Account";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/devices" element={<DeviceList />} />
        <Route path="/devices/new" element={<AddDevice />} />
        <Route path="/devices/:devEui" element={<DeviceDetail />} />
        <Route path="/devices/:devEui/sticker" element={<StickerView />} />
        <Route path="/billing" element={<Billing />} />
        <Route path="/account" element={<Account />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
