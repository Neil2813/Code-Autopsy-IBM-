import { Outlet } from "react-router-dom";
import { PublicHeader } from "./PublicHeader";
import { Footer } from "./Footer";

export const PublicLayout = () => (
  <div className="flex min-h-screen flex-col bg-background text-foreground">
    <PublicHeader />
    <main className="flex-1"><Outlet /></main>
    <Footer />
  </div>
);