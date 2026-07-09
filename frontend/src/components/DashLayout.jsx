import { Link, useLocation, useNavigate } from "react-router-dom";
import { Navbar } from "./ui";
import { useAuth } from "../context/AuthContext";

export default function DashLayout({ title, nav = [], active, onNav, children, actions }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <>
      <Navbar />
      <div className="dash">
        <aside className="side">
          <div className="side-brand">{title}</div>
          {nav.map(item => (
            <a key={item.key} className={active === item.key ? "active" : ""}
               onClick={() => onNav(item.key)} style={{ cursor: "pointer" }}>
              <span>{item.icon}</span> {item.label}
            </a>
          ))}
          <a onClick={async () => { await logout(); navigate("/"); }} style={{ cursor: "pointer", marginTop: 12 }}>↩ Sign out</a>
        </aside>
        <main className="main">
          <div className="page-h">
            <div>
              <div className="muted" style={{ fontSize: ".82rem", fontFamily: "var(--head)", letterSpacing: ".04em", textTransform: "uppercase" }}>{user?.email}</div>
              <h1>{nav.find(n => n.key === active)?.label || title}</h1>
            </div>
            {actions}
          </div>
          {children}
        </main>
      </div>
    </>
  );
}
