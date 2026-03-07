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
import Verification from "./pages/dashboard/Verification";
import Applications from "./pages/dashboard/Applications";
import DealCars from "./pages/dashboard/DealCars";
import PurchasedCars from "./pages/dashboard/PurchasedCars";
import Tracking from "./pages/dashboard/Tracking";
import Calculator from "./pages/Calculator";
import CatalogPage from "./pages/CatalogPage";
import CarDetailPage from "./pages/CarDetailPage";
import ContractorsPage from "./pages/ContractorsPage";
import ContractorRegisterPage from "./pages/ContractorRegisterPage";
import ContractorDashboard from "./pages/ContractorDashboard";
import ModeratorPage from "./pages/ModeratorPage";
import UserProfileModerator from "./pages/UserProfileModerator";
import HotDealsPage from "./pages/HotDealsPage";
import AffiliatePage from "./pages/AffiliatePage";
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
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/catalog/:carId" element={<CarDetailPage />} />
          <Route path="/contractors" element={<ContractorsPage />} />
          <Route path="/contractor-register" element={<ContractorRegisterPage />} />
          <Route path="/contractor-dashboard" element={<ContractorDashboard />} />
          <Route path="/moderator" element={<ModeratorPage />} />
          <Route path="/moderator/user/:userId" element={<UserProfileModerator />} />
          <Route path="/hot-deals" element={<HotDealsPage />} />
          <Route path="/partners" element={<AffiliatePage />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<DashboardOverview />} />
            <Route path="garage" element={<MyGarage />} />
            <Route path="applications" element={<Applications />} />
            <Route path="deals" element={<DealCars />} />
            <Route path="purchased" element={<PurchasedCars />} />
            <Route path="tenders" element={<Tenders />} />
            <Route path="verification" element={<Verification />} />
            <Route path="documents" element={<Documents />} />
            <Route path="tracking" element={<Tracking />} />
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
