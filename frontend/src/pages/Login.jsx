import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Navbar, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [sp] = useSearchParams();
  const [form, setForm] = useState({ email: "", password: "" });
  const [state, setState] = useState({ loading: false, error: null });

  const submit = async (e) => {
    e?.preventDefault();
    setState({ loading: true, error: null });
    try {
      const user = await login(form.email, form.password);
      const next = sp.get("next");
      if (next) nav(next);
      else nav(user.role === "candidate" ? "/candidate" : user.role === "employer" ? "/employer" : "/admin");
    } catch (err) {
      setState({ loading: false, error: err.message || "Login failed" });
    }
  };

  return (
    <>
      <Navbar />
      <div className="auth-wrap">
        <aside className="auth-aside">
          <span className="dot" />
          <h2>Welcome back</h2>
          <p>Sign in to manage your journey to Japan — track applications, interviews, and verification status in one place.</p>
          <ul>
            <li>Candidates: manage your profile & applications</li>
            <li>Employers: search verified, privacy-protected talent</li>
            <li>Admins: verify, match, and manage placements</li>
          </ul>
        </aside>
        <form className="auth-form" onSubmit={submit}>
          <h1 style={{ fontFamily: "var(--display)", fontSize: "2rem" }}>Log in</h1>
          <p className="muted mb-3">New here? <Link to="/register" style={{ color: "var(--red)", fontWeight: 600 }}>Create an account</Link></p>
          {state.error && <div className="alert alert-error">{state.error}</div>}
          <Field label="Email"><input className="input" type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></Field>
          <Field label="Password"><input className="input" type="password" required value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></Field>
          <button className="btn btn-primary btn-block" disabled={state.loading}>{state.loading ? "Signing in…" : "Log in"}</button>
          <div className="divider" />
          <p className="form-note">Demo — admin@japancareer.jp · candidate@example.com · employer@example.com (passwords in README)</p>
        </form>
      </div>
    </>
  );
}
