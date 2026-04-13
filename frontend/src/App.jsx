import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Analysis from "./pages/Analysis";
import CaseHistory from "./pages/CaseHistory";
import KnowledgeCenter from "./pages/KnowledgeCenter";
import Chatbot from "./pages/chatbot";
import Register from "./pages/Register";
import About from "./pages/About";

function ProtectedRoute({ children, isAuthenticated, checkingAuth }) {
  if (checkingAuth) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        Checking session...
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/" replace />;
}

function PublicRoute({ children, isAuthenticated, checkingAuth }) {
  if (checkingAuth) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        Checking session...
      </div>
    );
  }

  return isAuthenticated ? <Navigate to="/landing" replace /> : children;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const validateSession = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setIsAuthenticated(false);
        setCheckingAuth(false);
        return;
      }

      try {
        const response = await fetch("http://127.0.0.1:8000/user/profile", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          setIsAuthenticated(false);
        } else {
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error("Session validation failed:", error);
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setIsAuthenticated(false);
      } finally {
        setCheckingAuth(false);
      }
    };

    validateSession();
  }, []);

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: "#ffffff",
            color: "#173428",
            border: "1px solid #dcebe3",
            borderRadius: "12px",
            boxShadow: "0 10px 30px rgba(15, 31, 23, 0.08)",
            fontSize: "0.9rem",
            fontWeight: "500",
          },
          success: {
            iconTheme: {
              primary: "#159957",
              secondary: "#ffffff",
            },
          },
          error: {
            iconTheme: {
              primary: "#c83b3b",
              secondary: "#ffffff",
            },
          },
        }}
      />

      <Routes>
        <Route
          path="/"
          element={
            <PublicRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <Login />
            </PublicRoute>
          }
        />

        <Route
          path="/register"
          element={
            <PublicRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <Register />
            </PublicRoute>
          }
        />

        <Route
          path="/landing"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <Landing />
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/analysis"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <Analysis />
            </ProtectedRoute>
          }
        />

        <Route
          path="/history"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <CaseHistory />
            </ProtectedRoute>
          }
        />

        <Route
          path="/chatbot"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <Chatbot />
            </ProtectedRoute>
          }
        />

        <Route
          path="/knowledge"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <KnowledgeCenter />
            </ProtectedRoute>
          }
        />

        <Route
          path="/about"
          element={
            <ProtectedRoute
              isAuthenticated={isAuthenticated}
              checkingAuth={checkingAuth}
            >
              <About />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;