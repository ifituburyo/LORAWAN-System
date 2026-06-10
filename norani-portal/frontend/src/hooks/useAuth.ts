import { useEffect, useState } from "react";
import type { User } from "../api/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem("norani_user");
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    // Re-sync on storage changes (multi-tab)
    const onStorage = () => {
      const raw = localStorage.getItem("norani_user");
      setUser(raw ? JSON.parse(raw) : null);
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const signIn = (token: string, user: User) => {
    localStorage.setItem("norani_token", token);
    localStorage.setItem("norani_user", JSON.stringify(user));
    setUser(user);
  };

  const signOut = () => {
    localStorage.removeItem("norani_token");
    localStorage.removeItem("norani_user");
    setUser(null);
  };

  return { user, signIn, signOut, isAuthenticated: !!user };
}
