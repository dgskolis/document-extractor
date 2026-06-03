import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "text-sm font-medium transition-colors hover:text-foreground",
    isActive ? "text-primary" : "text-muted-foreground",
  );

export default function Header() {
  return (
    <header className="border-b border-border bg-background">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:gap-6 md:px-6">
        <span className="text-lg font-semibold text-foreground">GenHealth</span>
        <nav className="flex gap-4">
          <NavLink to="/" className={navLinkClass} end>
            Orders
          </NavLink>
          <NavLink to="/upload" className={navLinkClass}>
            Upload
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
