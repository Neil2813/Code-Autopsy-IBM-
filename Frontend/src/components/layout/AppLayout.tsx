import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";

export const AppLayout = () => (
  <div className="flex min-h-screen bg-background text-foreground overflow-hidden">
    <AppSidebar />
    <div className="flex min-w-0 flex-1 flex-col h-screen overflow-y-auto">
      <main className="flex-1 px-6 py-8 md:px-10 md:py-10">
        <Outlet />
      </main>
    </div>
  </div>
);