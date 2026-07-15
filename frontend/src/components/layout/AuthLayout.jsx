import { ThemeToggle } from "../ui/ThemeToggle.jsx";

export function AuthLayout({ children, showBrand = true }) {
  return (
    <main className="layout-auth">
      <div className="layout-auth__card">
        <ThemeToggle className="layout-auth__theme-toggle" />
        {showBrand ? (
          <div className="layout-auth__brand">
            <div className="layout-auth__logo">R</div>
            <div className="layout-auth__name">Reps</div>
          </div>
        ) : null}
        {children}
      </div>
    </main>
  );
}
