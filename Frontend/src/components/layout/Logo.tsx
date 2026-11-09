import { Link } from "react-router-dom";

export const Logo = ({
  to = "/",
  className = "",
  showSubtitle = false,
}: {
  to?: string;
  className?: string;
  showSubtitle?: boolean;
}) => (
  <Link to={to} className="flex items-center gap-2.5 group select-none">
    <div className="relative flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-primary/10 p-1 border border-primary/20 shadow-sm transition-all duration-300 group-hover:scale-105 group-hover:border-primary/40 group-hover:shadow-primary/20">
      <img src="/Logo.png" alt="Logo" className="h-full w-full object-contain" />
    </div>
    <div className="flex flex-col">
      <span
        className={`text-lg font-bold tracking-tight transition-colors group-hover:text-primary font-heading leading-none ${
          className || "text-foreground"
        }`}
      >
        Code Autopsy
      </span>
      {showSubtitle && (
        <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-widest leading-none mt-1">
          Legacy AI Copilot
        </span>
      )}
    </div>
  </Link>
);
