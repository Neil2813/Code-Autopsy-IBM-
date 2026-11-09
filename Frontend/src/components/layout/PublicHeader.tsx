import { Link } from "react-router-dom";
import { Logo } from "./Logo";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/lib/store/useAppStore";
import { ArrowRight, BookOpen, Sparkles } from "lucide-react";

export const PublicHeader = () => {
  const { isAuthenticated } = useAppStore();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-black/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Logo className="text-white" showSubtitle={true} />
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <Link
              to="/"
              className="text-white/70 hover:text-white transition-colors font-medium tracking-wide"
            >
              Overview
            </Link>
            <Link
              to="/about"
              className="text-white/70 hover:text-white transition-colors font-medium tracking-wide"
            >
              About
            </Link>
            <Link
              to="/docs"
              className="text-white/70 hover:text-white transition-colors font-medium tracking-wide flex items-center gap-1.5"
            >
              <BookOpen className="h-3.5 w-3.5 text-primary" />
              Documentation
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <Button
              asChild
              size="sm"
              className="h-9 px-4 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-md shadow-primary/20 transition-all group"
            >
              <Link to="/dashboard" className="flex items-center gap-2">
                <span>Console</span>
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </Button>
          ) : (
            <>
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="h-9 text-white/80 hover:text-white hover:bg-white/10 rounded-xl font-medium"
              >
                <Link to="/login">Sign In</Link>
              </Button>
              <Button
                asChild
                size="sm"
                className="h-9 px-4 rounded-xl bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/95 hover:to-indigo-600/95 text-white font-semibold shadow-md shadow-primary/25 transition-all group"
              >
                <Link to="/register" className="flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-200" />
                  <span>Start Audit</span>
                </Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
