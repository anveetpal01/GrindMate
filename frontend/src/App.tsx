import { Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "@/pages/Login";
import { SignupPage } from "@/pages/Signup";
import { JoinPage } from "@/pages/Join";
import { VerifyEmailPage } from "@/pages/VerifyEmail";
import { VerifyOtpPage } from "@/pages/VerifyOtp";
import { ForgotPasswordPage } from "@/pages/ForgotPassword";
import { ResetPasswordPage } from "@/pages/ResetPassword";
import { DashboardPage } from "@/pages/Dashboard";
import { AccountPage } from "@/pages/Account";
import { GroupsPage } from "@/pages/Groups";
import { GroupDetailPage } from "@/pages/GroupDetail";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/verify-otp" element={<VerifyOtpPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
      <Route path="/join/:token" element={<JoinPage />} />

      {/* Authenticated routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/groups" element={<GroupsPage />} />
          <Route path="/groups/:publicId" element={<GroupDetailPage />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
