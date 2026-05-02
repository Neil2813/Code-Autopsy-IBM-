import { Link, Outlet } from "react-router-dom";
import { Logo } from "@/components/layout/Logo";

export const AuthLayout = () => (
  <div className="flex min-h-screen flex-col bg-gradient-subtle">
    <header className="container flex h-16 items-center">
      <Logo />
    </header>
    <main className="flex flex-1 items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </main>
    <footer className="container py-6 text-center text-xs text-muted-foreground">
      <Link to="/" className="hover:text-foreground">Back to home</Link>
    </footer>
  </div>
);