import { Link } from "react-router-dom";

export const Footer = () => (
  <footer className="border-t border-white/5 bg-[#000000]">
    <div className="container flex flex-col items-center justify-between gap-4 py-8 md:flex-row">
      <p className="text-sm text-muted-foreground">
        © {new Date().getFullYear()} Code Autopsy · Built for enterprise legacy modernization.
      </p>
      <div className="flex items-center gap-6 text-sm text-muted-foreground">
        <Link to="/about" className="hover:text-foreground">About</Link>
        <Link to="/docs" className="hover:text-foreground">Docs</Link>
      </div>
    </div>
  </footer>
);