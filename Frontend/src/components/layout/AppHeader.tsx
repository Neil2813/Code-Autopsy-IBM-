import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Menu,
  Plus,
  Moon,
  Sun,
  Search,
  ChevronRight,
  User as UserIcon,
  Settings,
  LogOut,
} from "lucide-react";
import { useAppStore } from "@/lib/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { SidebarContent } from "./AppSidebar";
import { Logo } from "./Logo";

export const AppHeader = () => {
  const { user, logout, theme, toggleTheme } = useAppStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const initials =
    user?.name
      ?.split(" ")
      .map((p) => p[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "NE";

  // Compute breadcrumb trail from pathname
  const path = location.pathname;
  let section = "Workspace";
  let page = "Dashboard";
  let subpage: string | null = null;

  if (path.startsWith("/upload")) {
    section = "Analysis";
    page = "New Analysis";
  } else if (path.startsWith("/history")) {
    section = "Workspace";
    page = "Audit History";
  } else if (path.startsWith("/analysis/")) {
    section = "Analysis";
    page = "Job Details";
    if (path.endsWith("/query")) {
      subpage = "Query Assistant";
    } else if (path.endsWith("/report")) {
      subpage = "Modernization Report";
    }
  } else if (path.startsWith("/settings")) {
    section = "Preferences";
    page = "Settings";
  } else if (path.startsWith("/profile")) {
    section = "Preferences";
    page = "User Profile";
  } else if (path.startsWith("/docs")) {
    section = "Resources";
    page = "Documentation";
  }

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-border/40 bg-background/80 px-4 sm:px-6 lg:px-8 backdrop-blur-xl transition-all duration-300">
      {/* Left: Mobile Menu + Breadcrumbs */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Mobile Sidebar Sheet Trigger */}
        <div className="lg:hidden">
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-xl hover:bg-muted/80 text-foreground"
                aria-label="Open navigation menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-72 sm:w-80 border-r border-border/50 bg-card">
              <SidebarContent onItemClick={() => setMobileMenuOpen(false)} />
            </SheetContent>
          </Sheet>
        </div>

        {/* Mobile Logo fallback */}
        <div className="lg:hidden flex items-center">
          <Logo to="/dashboard" />
        </div>

        {/* Desktop Breadcrumbs */}
        <div className="hidden lg:flex items-center gap-2 text-sm">
          <span className="text-muted-foreground/70 font-medium">{section}</span>
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40" />
          <span className="font-semibold text-foreground tracking-tight">{page}</span>
          {subpage && (
            <>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40" />
              <Badge variant="secondary" className="font-medium text-xs bg-primary/10 text-primary border-primary/20">
                {subpage}
              </Badge>
            </>
          )}
        </div>
      </div>

      {/* Right: Quick Search, Status, CTAs & User Menu */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Quick Search Trigger Pill */}
        <button
          onClick={() => navigate("/history")}
          className="hidden md:flex items-center gap-2.5 h-9 rounded-xl border border-border/60 bg-muted/30 px-3.5 text-xs text-muted-foreground hover:bg-muted/60 hover:text-foreground transition-all duration-200"
        >
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="font-medium">Search audits & code...</span>
          <kbd className="pointer-events-none hidden lg:inline-flex h-5 select-none items-center gap-1 rounded border border-border/60 bg-background/50 px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            ⌘K
          </kbd>
        </button>

        {/* Quick New Analysis Action Button */}
        <Button
          asChild
          size="sm"
          className="h-9 px-3.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-sm shadow-primary/25 transition-all group"
        >
          <Link to="/upload" className="flex items-center gap-1.5">
            <Plus className="h-4 w-4 transition-transform group-hover:rotate-90 duration-200" />
            <span className="hidden sm:inline text-xs font-semibold">New Analysis</span>
          </Link>
        </Button>

        {/* Theme Toggle Button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="h-9 w-9 rounded-xl hover:bg-muted/80 text-foreground transition-colors"
          title="Toggle Light/Dark Theme"
        >
          {theme === "light" ? (
            <Moon className="h-4 w-4 text-slate-700 hover:rotate-12 transition-transform" />
          ) : (
            <Sun className="h-4 w-4 text-amber-400 hover:rotate-45 transition-transform" />
          )}
        </Button>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-xl p-0 hover:ring-2 hover:ring-primary/20 transition-all"
            >
              <Avatar className="h-8 w-8 border border-border/70">
                <AvatarFallback className="bg-primary/15 text-primary text-xs font-bold font-heading">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="w-56 p-2 mt-1 shadow-2xl border-border/60 bg-popover/95 backdrop-blur-md rounded-xl"
          >
            <DropdownMenuLabel className="font-normal px-2 py-1.5">
              <div className="flex flex-col space-y-0.5">
                <p className="text-sm font-bold text-foreground">{user?.name || "Enterprise User"}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email || "architect@enterprise.ibm"}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="my-1.5" />
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-xs font-medium focus:bg-accent"
              onClick={() => navigate("/profile")}
            >
              <UserIcon className="mr-2.5 h-3.5 w-3.5 text-muted-foreground" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-xs font-medium focus:bg-accent"
              onClick={() => navigate("/settings")}
            >
              <Settings className="mr-2.5 h-3.5 w-3.5 text-muted-foreground" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator className="my-1.5" />
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-xs font-medium text-destructive focus:text-destructive focus:bg-destructive/10"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut className="mr-2.5 h-3.5 w-3.5 text-destructive/70" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};
