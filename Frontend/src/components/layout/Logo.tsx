import { Link } from "react-router-dom";

export const Logo = ({ to = "/", className = "" }: { to?: string; className?: string }) => (
  <Link to={to} className="flex items-center gap-3 group">
    <div className="flex h-9 w-9 items-center justify-center overflow-hidden transition-transform duration-200 group-hover:scale-110">
      <img src="/Logo.png" alt="Logo" className="h-full w-full object-contain" />
    </div>
    <span className={`text-xl font-bold tracking-tight transition-colors group-hover:text-primary font-heading ${className || "text-foreground"}`}>
      Code Autopsy
    </span>
  </Link>
);
