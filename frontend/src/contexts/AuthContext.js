import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('carbridge_token'));
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('carbridge_token');
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        } catch (error) {
          logout();
        }
      }
      setLoading(false);
    };
    verifyToken();
  }, [token, logout]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('carbridge_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (data) => {
    const response = await axios.post(`${API}/auth/register`, data);
    const { access_token, user: userData } = response.data;
    localStorage.setItem('carbridge_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
