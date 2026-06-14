import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { HomePage } from "./pages/HomePage";
import { RoleDashboardPage } from "./pages/RoleDashboardPage";
import { InspectorLandingPage } from "./pages/InspectorLandingPage";
import { FacilityDetailPage } from "./pages/FacilityDetailPage";
import { InstancesPage } from "./pages/InstancesPage";
import { InstanceDetailPage } from "./pages/InstanceDetailPage";
import { TasksPage } from "./pages/TasksPage";
import { ChecklistsPage } from "./pages/ChecklistsPage";
import { ChecklistRunDetailPage } from "./pages/ChecklistRunDetailPage";
import { CompliancePage } from "./pages/CompliancePage";
import { FinancialsPage } from "./pages/FinancialsPage";
import { FacilitiesPage } from "./pages/FacilitiesPage";
import { FacilityDirectoryDetailPage } from "./pages/FacilityDirectoryDetailPage";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password/:uid/:token" element={<ResetPasswordPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <RoleDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/my-assignments"
          element={
            <ProtectedRoute>
              <InspectorLandingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/my-assignments/facilities/:facilityId"
          element={
            <ProtectedRoute>
              <FacilityDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/instances"
          element={
            <ProtectedRoute>
              <InstancesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/instances/:id"
          element={
            <ProtectedRoute>
              <InstanceDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks"
          element={
            <ProtectedRoute>
              <TasksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checklists"
          element={
            <ProtectedRoute>
              <ChecklistsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checklists/:id"
          element={
            <ProtectedRoute>
              <ChecklistRunDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/compliance"
          element={
            <ProtectedRoute>
              <CompliancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/financials"
          element={
            <ProtectedRoute>
              <FinancialsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/facilities"
          element={
            <ProtectedRoute>
              <FacilitiesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/facilities/:facilityId"
          element={
            <ProtectedRoute>
              <FacilityDirectoryDetailPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
