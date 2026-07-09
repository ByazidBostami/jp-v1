import { Link, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export function Spinner() { return <div className="spinner" role="status" aria-label="Loading" />; }

const STATUS_TONE = {
  verified: "green", approved: "green", published: "green", passed: "green", active: "green",
  selected: "green", deployed: "green", open: "green",
  pending: "orange", pending_verification: "orange", correction_required: "orange",
  incomplete: "orange", draft: "orange", scheduled: "orange", new: "orange",
  rejected: "red", suspended: "red", failed: "red", closed: "red", inactive: "red", withdrawn: "red",
};
export function Badge({ status, children }) {
  const tone = STATUS_TONE[status] || "blue";
  const label = (children || status || "").toString().replace(/_/g, " ");
  return <span className={`badge badge-${tone}`}>{label}</span>;
}

export function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const dash = user
    ? user.role === "candidate" ? "/candidate"
      : user.role === "employer" ? "/employer"
      : "/admin"
    : null;
  return (
    <header className="nav">
      <div className="container nav-inner">
        <Link to="/" className="brand"><span className="dot" />Japan<span className="jp">Career</span>.jp</Link>
        <nav className={`nav-links ${open ? "open" : ""}`} onClick={() => setOpen(false)}>
          <Link to="/jobs">Browse Jobs</Link>
          <Link to="/#programs">Programs</Link>
          <Link to="/#how">How it works</Link>
          <Link to="/about">About</Link>
        </nav>
        <div className="nav-actions">
          {user ? (
            <>
              <Link className="btn btn-ghost btn-sm" to={dash}>Dashboard</Link>
              <button className="btn btn-primary btn-sm" onClick={async () => { await logout(); nav("/"); }}>Sign out</button>
            </>
          ) : (
            <>
              <Link className="btn btn-ghost btn-sm" to="/login">Log in</Link>
              <Link className="btn btn-primary btn-sm" to="/register">Get started</Link>
            </>
          )}
          <button className="nav-toggle" onClick={() => setOpen(o => !o)} aria-label="Menu">☰</button>
        </div>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="brand" style={{ fontSize: "1.3rem" }}>Japan<span style={{ color: "var(--red)" }}>Career</span>.jp</div>
            <p style={{ maxWidth: "34ch" }}>The securely managed bridge connecting Japan-ready talent from Bangladesh with employers and educators across Japan.</p>
          </div>
          <div>
            <h4>Candidates</h4>
            <Link to="/register">Create profile</Link>
            <Link to="/jobs">Browse jobs</Link>
            <Link to="/#programs">Programs</Link>
          </div>
          <div>
            <h4>Employers</h4>
            <Link to="/register">Register company</Link>
            <Link to="/login">Search talent</Link>
            <Link to="/about">How hiring works</Link>
          </div>
          <div>
            <h4>Company</h4>
            <Link to="/about">About us</Link>
            <Link to="/contact">Contact</Link>
            <Link to="/login">Admin</Link>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} JapanCareer.jp — All rights reserved.</span>
          <span className="credit">Developed by <a href="https://softyit.com" target="_blank" rel="noreferrer">SoftyIT (softyit.com)</a></span>
        </div>
      </div>
    </footer>
  );
}

export function PublicLayout({ children }) {
  return (<><Navbar />{children}<Footer /></>);
}

export function ProtectedRoute({ role, children }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div style={{ minHeight: "60vh" }}><Spinner /></div>;
  if (!user) return <RedirectTo to={`/login?next=${encodeURIComponent(loc.pathname)}`} />;
  if (role && user.role !== role) return <RedirectTo to="/" />;
  return children;
}

import { Navigate } from "react-router-dom";
function RedirectTo({ to }) { return <Navigate to={to} replace />; }

export function Field({ label, children, note }) {
  return (
    <div className="field">
      {label && <label>{label}</label>}
      {children}
      {note && <div className="form-note mt-1">{note}</div>}
    </div>
  );
}

export function money(min, max, cur = "JPY", type = "monthly") {
  const f = n => n ? Number(n).toLocaleString() : null;
  if (!min && !max) return "Negotiable";
  const range = min && max ? `${f(min)}–${f(max)}` : f(min || max);
  return `¥${range} / ${type.replace("ly", "")}`;
}
