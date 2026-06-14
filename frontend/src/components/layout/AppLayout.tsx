import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import type { UserRole } from "../../types";

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrator",
  director_manager: "Director/Manager",
  supervisor: "Supervisor",
  inspector: "Inspector",
  it_staff: "IT Staff",
  support_staff: "Support Staff",
  readonly: "Read Only",
};

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

const mainNav: NavItem[] = [
  {
    to: "/",
    label: "Home",
    icon: (
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
    ),
  },
  {
    to: "/dashboard",
    label: "Dashboard",
    icon: (
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>
    ),
  },
  {
    to: "/instances",
    label: "Requests",
    icon: (
      <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
    ),
  },
  {
    to: "/tasks",
    label: "Tasks",
    icon: (
      <svg viewBox="0 0 24 24"><path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
    ),
  },
  {
    to: "/checklists",
    label: "Checklists",
    icon: (
      <svg viewBox="0 0 24 24"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
    ),
  },
];

const opsNav: NavItem[] = [
  {
    to: "/compliance",
    label: "Compliance",
    icon: <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>,
  },
  {
    to: "/financials",
    label: "Financials",
    icon: <svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>,
  },
  {
    to: "/facilities",
    label: "Facilities",
    icon: <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>,
  },
];

interface AppLayoutProps {
  title: string;
  breadcrumb?: string[];
  actions?: ReactNode;
  children: ReactNode;
}

export function AppLayout({ title, breadcrumb, actions, children }: AppLayoutProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const initial = (user?.first_name || user?.username || "?").slice(0, 1).toUpperCase();

  return (
    <>
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><path d="M14 17.5h7M17.5 14v7" /></svg>
          </div>
          <span>FJ<em>ADMIN</em></span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">Main</div>
          {mainNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}

          {(user?.role === "inspector" || user?.is_inspector) && (
            <>
              <div className="nav-section">Inspector</div>
              <NavLink
                to="/my-assignments"
                className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
              >
                <svg viewBox="0 0 24 24"><path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
                My Assignments
              </NavLink>
            </>
          )}

          <div className="nav-section">Operations</div>
          {opsNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}

          {user?.is_staff && (
            <>
              <div className="nav-section">Admin</div>
              <a href="/admin/" className="nav-link">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
                Admin Panel
              </a>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="user-avatar">{initial}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="user-name">{user?.full_name || user?.username}</div>
              <div className="user-role">
                {user?.role
                  ? ROLE_LABELS[user.role]
                  : user?.is_staff
                    ? "Administrator"
                    : user?.is_inspector
                      ? "Inspector"
                      : "User"}
              </div>
            </div>
            <button type="button" className="logout-btn" title="Sign out" onClick={() => void handleLogout()}>
              <svg style={{ width: 15, height: 15, fill: "none", stroke: "currentColor", strokeWidth: 2 }} viewBox="0 0 24 24">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      <div className="page-root">
        <div className="topbar">
          <div style={{ flex: 1, minWidth: 0 }}>
            {breadcrumb && breadcrumb.length > 0 && (
              <div className="topbar-breadcrumb">
                {breadcrumb.map((crumb) => (
                  <span key={crumb}>{crumb}</span>
                ))}
              </div>
            )}
            <div className="topbar-title">{title}</div>
          </div>
          {actions}
        </div>

        <div className="page-body">{children}</div>
      </div>
    </>
  );
}
