import { NavLink } from "react-router-dom";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
        <span className="text-lg font-semibold text-gray-900">GenHealth</span>
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
