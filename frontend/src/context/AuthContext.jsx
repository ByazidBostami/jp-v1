import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, setTokens, clearTokens, hasToken } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    if (!hasToken()) { setUser(null); setLoading(false); return null; }
    try {
      const res = await api.get("/auth/me");
      setUser(res.data);
      return res.data;
    } catch {
      clearTokens();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refreshMe(); }, [refreshMe]);

  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password }, { auth: false });
    setTokens(res.data.tokens);
    setUser(res.data.user);
    // fetch full profile block
    await refreshMe();
    return res.data.user;
  };

  const logout = async () => {
    try { await api.post("/auth/logout", {}); } catch { /* ignore */ }
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshMe, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
