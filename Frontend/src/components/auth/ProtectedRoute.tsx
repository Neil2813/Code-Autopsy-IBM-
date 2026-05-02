import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAppStore } from "@/lib/store/useAppStore";

export const ProtectedRoute = () => {
  const isAuthenticated = useAppStore((s) => s.isAuthenticated);
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
};