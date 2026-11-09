import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Plus,
  History as HistoryIcon,
  UploadCloud,
  Settings,
  User as UserIcon,
  LogOut,
  Moon,
  Sun,
  BookOpen,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";
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

interface SidebarContentProps {
  onItemClick?: () => void;
}

export const SidebarContent = ({ onItemClick }: SidebarContentProps) => {
  const { user, logout, theme, toggleTheme, currentJobId } = useAppStore();
  const navigate = useNavigate();
  const initials =
    user?.name
      ?.split(" ")
      .map((p) => p[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "NE";

  const navGroups = [
    {
      title: "Workspace",
      items: [
        {
          to: "/dashboard",
          label: "Dashboard",
          icon: LayoutDashboard,
          badge: null,
        },
        {
          to: "/history",
          label: "Audit History",
          icon: HistoryIcon,
          badge: null,
        },
      ],
    },
    {
      title: "Analysis & Modernization",
      items: [
        {
          to: "/upload",
          label: "Upload Codebase",
          icon: UploadCloud,
          badge: null,
        },
        ...(currentJobId
          ? [
              {
                to: `/analysis/${currentJobId}`,
                label: "Current Analysis",
                icon: Sparkles,
                badge: "Active",
              },
            ]
          : []),
        {
          to: "/docs",
          label: "Documentation",
          icon: BookOpen,
          badge: null,
        },
      ],
    },
    {
      title: "Preferences",
      items: [
        {
          to: "/settings",
          label: "Settings",
          icon: Settings,
          badge: null,
        },
        {
          to: "/profile",
          label: "Profile",
          icon: UserIcon,
          badge: null,
        },
      ],
    },
  ];

  return (
    <div className="flex h-full flex-col justify-between overflow-hidden">
      {/* Top Header / Logo */}
      <div>
        <div className="flex h-20 items-center justify-between px-6 border-b border-border/40 bg-card/30 backdrop-blur-sm">
          <Logo to="/dashboard" />
          <Badge
            variant="outline"
            className="border-primary/20 bg-primary/5 text-primary text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full"
          >
            v2.0
          </Badge>
        </div>

        {/* Primary Action Button */}
        <div className="p-4 pb-2">
          <Button
            asChild
            className="w-full h-11 justify-start gap-2.5 rounded-xl bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/95 hover:to-indigo-600/95 text-primary-foreground font-semibold shadow-md shadow-primary/20 transition-all duration-300 group"
            onClick={onItemClick}
          >
            <Link to="/upload">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-white/20 text-white transition-transform group-hover:rotate-90 duration-300">
                <Plus className="h-4 w-4" />
              </div>
              <span className="text-sm font-medium tracking-wide">New Analysis</span>
              <ChevronRight className="ml-auto h-4 w-4 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
            </Link>
          </Button>
        </div>

        {/* Navigation Groups */}
        <nav className="space-y-6 px-3 py-3 overflow-y-auto max-h-[calc(100vh-340px)] custom-scrollbar">
          {navGroups.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="px-3 pb-1.5 text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 font-sans">
                {group.title}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      onClick={onItemClick}
                      className={({ isActive }) =>
                        cn(
                          "relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200 group",
                          isActive
                            ? "bg-primary/10 text-primary font-semibold shadow-sm shadow-primary/5 before:absolute before:left-0 before:top-2 before:bottom-2 before:w-1 before:rounded-r-full before:bg-primary"
                            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                        )
                      }
                    >
                      <Icon className="h-4 w-4 shrink-0 transition-colors group-hover:text-primary" />
                      <span className="truncate">{item.label}</span>
                      {item.badge && (
                        <Badge
                          variant="secondary"
                          className="ml-auto text-[10px] px-1.5 py-0 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-medium"
                        >
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse" />
                          {item.badge}
                        </Badge>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Footer Area */}
      <div className="p-4 space-y-3 border-t border-border/40 bg-card/40 backdrop-blur-sm">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Theme</span>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-8 w-8 rounded-lg hover:bg-muted/80 text-foreground transition-colors"
            title="Toggle Light/Dark Theme"
          >
            {theme === "light" ? (
              <Moon className="h-4 w-4 text-slate-700" />
            ) : (
              <Sun className="h-4 w-4 text-amber-400" />
            )}
          </Button>
        </div>

        {/* User Card & Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="w-full flex items-center justify-between p-2 h-auto hover:bg-muted/60 rounded-xl transition-all border border-transparent hover:border-border/40"
            >
              <div className="flex items-center gap-3 truncate">
                <Avatar className="h-9 w-9 border border-border/60 ring-2 ring-primary/10">
                  <AvatarFallback className="bg-primary/15 text-primary text-xs font-bold font-heading">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-col items-start truncate text-left">
                  <span className="text-xs font-bold truncate leading-tight text-foreground">
                    {user?.name || "Enterprise User"}
                  </span>
                  <span className="text-[11px] text-muted-foreground truncate leading-tight">
                    {user?.email || "architect@enterprise.ibm"}
                  </span>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground/60 shrink-0" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            side="right"
            className="w-64 p-2 ml-2 shadow-2xl border-border/60 bg-popover/95 backdrop-blur-md rounded-xl"
          >
            <DropdownMenuLabel className="font-normal px-2 py-2">
              <div className="flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-bold leading-none text-foreground">{user?.name || "Enterprise User"}</p>
                  <Badge variant="outline" className="text-[10px] py-0 px-1 border-primary/30 text-primary">
                    Lead Architect
                  </Badge>
                </div>
                <p className="text-xs leading-none text-muted-foreground">{user?.email || "architect@enterprise.ibm"}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="my-1.5" />
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-sm focus:bg-accent group"
              onClick={() => {
                navigate("/profile");
                onItemClick?.();
              }}
            >
              <UserIcon className="mr-3 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              User Profile
            </DropdownMenuItem>
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-sm focus:bg-accent group"
              onClick={() => {
                navigate("/settings");
                onItemClick?.();
              }}
            >
              <Settings className="mr-3 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              Settings & Integrations
            </DropdownMenuItem>
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-sm focus:bg-accent group"
              onClick={() => {
                navigate("/docs");
                onItemClick?.();
              }}
            >
              <BookOpen className="mr-3 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              API Documentation
            </DropdownMenuItem>
            <DropdownMenuSeparator className="my-1.5" />
            <DropdownMenuItem
              className="rounded-lg cursor-pointer py-2 text-sm text-destructive focus:text-destructive focus:bg-destructive/10 group"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut className="mr-3 h-4 w-4 text-destructive/70 group-hover:text-destructive transition-colors" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export const AppSidebar = () => {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-border/40 bg-card/60 backdrop-blur-xl lg:flex lg:flex-col h-screen sticky top-0 z-30 transition-all duration-300">
      <SidebarContent />
    </aside>
  );
};
