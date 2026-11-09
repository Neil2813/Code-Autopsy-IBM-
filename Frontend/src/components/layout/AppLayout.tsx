import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";
import { AppHeader } from "./AppHeader";

export const AppLayout = () => (
  <div className="flex min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
    {/* Desktop Sticky Sidebar */}
    <AppSidebar />

    {/* Main View Area */}
    <div className="flex min-w-0 flex-1 flex-col min-h-screen bg-background">
      {/* Top Navigation Bar with Breadcrumbs & Actions */}
      <AppHeader />

      {/* Main Content with Ambient Backdrop Glow */}
      <main className="relative flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
        {/* Subtle Ambient Radial Lighting */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-96 -z-10 overflow-hidden opacity-60 dark:opacity-30 blur-3xl"
        >
          <div className="mx-auto h-full max-w-7xl bg-gradient-to-b from-primary/15 via-indigo-500/5 to-transparent" />
        </div>

        <div className="mx-auto w-full max-w-7xl animate-in fade-in duration-300">
          <Outlet />
        </div>
      </main>
    </div>
  </div>
);
