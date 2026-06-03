import { Outlet } from "react-router-dom";

import Header from "./Header";

export default function AppShell() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto min-w-0 max-w-5xl px-4 py-8 md:px-6">
        <Outlet />
      </main>
    </div>
  );
}
