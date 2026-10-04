import React, { createContext, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { TOKEN_KEY } from "./api.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [email, setEmail] = useState(() => localStorage.getItem("slp_email") || "");

  const login = async (emailInput, password) => {
    const { data } = await api.post("/api/auth/login", { email: emailInput, password });
    // Prototype choice: JWT kept in localStorage (documented in docs/ARCHITECTURE.md). Tokens expire after JWT_EXPIRE_MINUTES.
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem("slp_email", data.user_email);
    setToken(data.access_token);
    setEmail(data.user_email);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("slp_email");
    setToken(null);
    setEmail("");
    navigate("/login");
  };

  useEffect(() => {
    const onUnauthorized = () => {
      setToken(null);
      navigate("/login");
    };
    window.addEventListener("slp-unauthorized", onUnauthorized);
    return () => window.removeEventListener("slp-unauthorized", onUnauthorized);
  }, [navigate]);

  return <AuthContext.Provider value={{ token, email, login, logout, isAuthenticated: !!token }}>{children}</AuthContext.Provider>;
}
