import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutGrid,
  Plus,
  History,
  Settings,
  User as UserIcon,
  LogOut,
  Moon,
  Sun,
} from "lucide-react";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const items = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "New analysis" },
  { to: "/history", label: "History" },
  { to: "/settings", label: "Settings" },
];

export const AppSidebar = () => {
  const { user, logout, theme, toggleTheme } = useAppStore();
  const navigate = useNavigate();
  const initials = user?.name?.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase() || "NE";

  return (
    <aside className="hidden w-72 shrink-0 border-r border-border/40 bg-card lg:flex lg:flex-col h-screen sticky top-0 transition-all duration-300">
      <div className="flex h-20 items-center px-8">
        <Logo to="/dashboard" />
      </div>
      
      <nav className="flex-1 space-y-1.5 p-6 pt-2">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center rounded-xl px-4 py-3 text-[15px] font-medium transition-all duration-200 group",
                isActive
                  ? "bg-primary/5 text-primary"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-6 mt-auto border-t border-border/40 space-y-4">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Theme</span>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={toggleTheme} 
            className="h-8 w-8 rounded-lg hover:bg-primary/10 transition-all group"
          >
            {theme === "light" ? (
              <Moon className="h-4 w-4 text-slate-700 group-hover:rotate-12 transition-transform" />
            ) : (
              <Sun className="h-4 w-4 text-amber-400 group-hover:rotate-45 transition-transform" />
            )}
          </Button>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="w-full flex items-center justify-start gap-3 p-2 h-auto hover:bg-muted/50 rounded-xl transition-all">
              <Avatar className="h-9 w-9 border border-border/50">
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-bold">{initials}</AvatarFallback>
              </Avatar>
              <div className="flex flex-col items-start truncate">
                <span className="text-sm font-bold truncate leading-tight">{user?.name || "Neil"}</span>
                <span className="text-[11px] text-muted-foreground truncate leading-tight">View profile</span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" side="right" className="w-60 p-2 ml-2 shadow-2xl border-border/50">
            <DropdownMenuLabel className="font-normal px-2 py-2">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-bold leading-none">{user?.name || "Neil"}</p>
                <p className="text-xs leading-none text-muted-foreground">{user?.email || "neil@example.com"}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="my-2" />
            <DropdownMenuItem className="rounded-md cursor-pointer py-2.5 focus:bg-accent group" onClick={() => navigate("/profile")}>
              <UserIcon className="mr-3 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem className="rounded-md cursor-pointer py-2.5 text-destructive focus:text-destructive focus:bg-destructive/10 group" onClick={() => { logout(); navigate("/login"); }}>
              <LogOut className="mr-3 h-4 w-4 text-destructive/70 group-hover:text-destructive transition-colors" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
};