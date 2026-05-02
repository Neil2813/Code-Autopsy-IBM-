import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Moon, Sun, LogOut, User as UserIcon, Plus } from "lucide-react";
import { useAppStore } from "@/lib/store/useAppStore";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";

export const AppHeader = () => {
  const { user, logout, theme, toggleTheme } = useAppStore();
  const navigate = useNavigate();
  const initials = user?.name?.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase() || "NE";

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-border/50 bg-card/80 px-6 backdrop-blur-md transition-all duration-300">
      <div className="flex items-center">
        <div className="lg:hidden">
          <Link to="/dashboard" className="text-xl font-bold tracking-tight text-primary">Code Autopsy</Link>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <Button asChild size="sm" className="hidden sm:inline-flex bg-primary hover:bg-primary/90 text-primary-foreground font-medium px-4 shadow-sm">
          <Link to="/upload">
            <Plus className="mr-2 h-4 w-4" />
            New analysis
          </Link>
        </Button>
      </div>
    </header>
  );
};