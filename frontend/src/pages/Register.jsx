import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setTokens } from "../api";
import { Navbar, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const nav = useNavigate();
  const { refreshMe } = useAuth();
  const [role, setRole] = useState("candidate");
  const [state, setState] = useState({ loading: false, error: null, ok: null });
  const [c, setC] = useState({ full_name: "", email: "", mobile: "", password: "", confirm_password: "" });
  const [e, setE] = useState({ company_name_english: "", contact_person_name: "", email: "", telephone: "", password: "", confirm_password: "" });

  const submit = async (ev) => {
    ev?.preventDefault();
    setState({ loading: true, error: null, ok: null });
    try {
      if (role === "candidate") {
        if (c.password !== c.confirm_password) throw new Error("Passwords do not match.");
        const r = await api.post("/auth/candidate/register", c, { auth: false });
        if (r.data?.tokens) { setTokens(r.data.tokens); await refreshMe(); nav("/candidate"); return; }
        setState({ loading: false, error: null, ok: "Account created. You can now log in." });
        setTimeout(() => nav("/login"), 1200);
      } else {
        if (e.password !== e.confirm_password) throw new Error("Passwords do not match.");
        const r = await api.post("/auth/employer/register", e, { auth: false });
        setState({ loading: false, error: null, ok: "Company registered. Our team will review your account for approval — you'll be notified once approved." });
        if (r.data?.tokens) { setTokens(r.data.tokens); await refreshMe(); setTimeout(() => nav("/employer"), 1400); }
        else setTimeout(() => nav("/login"), 1600);
      }
    } catch (err) {
      const detail = err.errors ? Object.values(err.errors).flat().join(" ") : err.message;
      setState({ loading: false, error: detail, ok: null });
    }
  };

  return (
    <>
      <Navbar />
      <div className="auth-wrap">
        <aside className="auth-aside">
          <span className="dot" />
          <h2>{role === "candidate" ? "Start your journey to Japan" : "Hire verified, Japan-ready talent"}</h2>
          <p>{role === "candidate"
            ? "Build a verified profile, get matched to real opportunities, and let our team guide you from application to departure."
            : "Access a pool of admin-verified candidates. Privacy-protected search, managed interviews, and full compliance support."}</p>
          <ul>
            {role === "candidate"
              ? <><li>Free profile & verification</li><li>Apply to real openings</li><li>Guided every step</li></>
              : <><li>Search verified candidates</li><li>Request managed interviews</li><li>Contact details stay protected</li></>}
          </ul>
        </aside>

        <form className="auth-form" onSubmit={submit}>
          <h1 style={{ fontFamily: "var(--display)", fontSize: "2rem" }}>Create your account</h1>
          <p className="muted mb-3">Already registered? <Link to="/login" style={{ color: "var(--red)", fontWeight: 600 }}>Log in</Link></p>

          <div className="flex gap-sm mb-3">
            <button type="button" className={`btn btn-sm ${role === "candidate" ? "btn-navy" : "btn-ghost"}`} onClick={() => setRole("candidate")}>I'm a candidate</button>
            <button type="button" className={`btn btn-sm ${role === "employer" ? "btn-navy" : "btn-ghost"}`} onClick={() => setRole("employer")}>I'm an employer</button>
          </div>

          {state.error && <div className="alert alert-error">{state.error}</div>}
          {state.ok && <div className="alert alert-ok">{state.ok}</div>}

          {role === "candidate" ? (
            <>
              <Field label="Full name"><input className="input" required value={c.full_name} onChange={ev => setC({ ...c, full_name: ev.target.value })} /></Field>
              <Field label="Email"><input className="input" type="email" required value={c.email} onChange={ev => setC({ ...c, email: ev.target.value })} /></Field>
              <Field label="Mobile"><input className="input" required value={c.mobile} onChange={ev => setC({ ...c, mobile: ev.target.value })} placeholder="+8801…" /></Field>
              <div className="grid cols-2" style={{ gap: 12 }}>
                <Field label="Password"><input className="input" type="password" required value={c.password} onChange={ev => setC({ ...c, password: ev.target.value })} /></Field>
                <Field label="Confirm"><input className="input" type="password" required value={c.confirm_password} onChange={ev => setC({ ...c, confirm_password: ev.target.value })} /></Field>
              </div>
            </>
          ) : (
            <>
              <Field label="Company name (English)"><input className="input" required value={e.company_name_english} onChange={ev => setE({ ...e, company_name_english: ev.target.value })} /></Field>
              <Field label="Contact person"><input className="input" required value={e.contact_person_name} onChange={ev => setE({ ...e, contact_person_name: ev.target.value })} /></Field>
              <div className="grid cols-2" style={{ gap: 12 }}>
                <Field label="Company email"><input className="input" type="email" required value={e.email} onChange={ev => setE({ ...e, email: ev.target.value })} /></Field>
                <Field label="Telephone"><input className="input" required value={e.telephone} onChange={ev => setE({ ...e, telephone: ev.target.value })} /></Field>
              </div>
              <div className="grid cols-2" style={{ gap: 12 }}>
                <Field label="Password"><input className="input" type="password" required value={e.password} onChange={ev => setE({ ...e, password: ev.target.value })} /></Field>
                <Field label="Confirm"><input className="input" type="password" required value={e.confirm_password} onChange={ev => setE({ ...e, confirm_password: ev.target.value })} /></Field>
              </div>
            </>
          )}
          <button className="btn btn-primary btn-block mt-2" disabled={state.loading}>{state.loading ? "Creating…" : "Create account"}</button>
        </form>
      </div>
    </>
  );
}
