import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./contexts/AuthContext";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DashboardLayout from "./layouts/DashboardLayout";
import DashboardOverview from "./pages/dashboard/DashboardOverview";
import MyGarage from "./pages/dashboard/MyGarage";
import Tenders from "./pages/dashboard/Tenders";
import Documents from "./pages/dashboard/Documents";
import Calculator from "./pages/Calculator";
import ProtectedRoute from "./components/ProtectedRoute";
import AIChat from "./components/AIChat";
import "@/App.css";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/calculator" element={<Calculator />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<DashboardOverview />} />
            <Route path="garage" element={<MyGarage />} />
            <Route path="tenders" element={<Tenders />} />
            <Route path="documents" element={<Documents />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <AIChat />
        <Toaster 
          position="top-right" 
          toastOptions={{
            style: {
              background: '#1C2128',
              border: '1px solid #27272A',
              color: '#F8FAFC',
            },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
