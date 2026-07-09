import { useState } from "react";
import { api } from "../api";
import { PublicLayout, Field } from "../components/ui";

export default function Contact() {
  const [form, setForm] = useState({ full_name: "", email: "", subject: "", message: "" });
  const [state, setState] = useState({ sending: false, msg: null });
  const submit = async () => {
    setState({ sending: true, msg: null });
    try {
      await api.post("/public/contact", form, { auth: false });
      setState({ sending: false, msg: { t: "ok", m: "Thanks — your message has reached our team. We'll be in touch." } });
      setForm({ full_name: "", email: "", subject: "", message: "" });
    } catch (e) {
      setState({ sending: false, msg: { t: "error", m: e.message } });
    }
  };
  return (
    <PublicLayout>
      <section className="section">
        <div className="container grid cols-2" style={{ alignItems: "start" }}>
          <div>
            <span className="eyebrow">Contact</span>
            <h1 className="mt-2" style={{ fontFamily: "var(--display)", fontSize: "2.3rem" }}>Talk to our team</h1>
            <p className="lead mt-2">Whether you're a candidate planning your move or an employer looking to hire, we're here to help.</p>
            <div className="mt-4">
              <Line k="Email" v="info@japancareer.jp" />
              <Line k="For employers" v="Register your company to access verified talent." />
              <Line k="For candidates" v="Create a profile and our team will guide you." />
            </div>
          </div>
          <div className="card card-pad">
            {state.msg && <div className={`alert ${state.msg.t === "ok" ? "alert-ok" : "alert-error"}`}>{state.msg.m}</div>}
            <Field label="Full name"><input className="input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} /></Field>
            <Field label="Email"><input className="input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></Field>
            <Field label="Subject"><input className="input" value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })} /></Field>
            <Field label="Message"><textarea className="input" rows={5} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} /></Field>
            <button className="btn btn-primary btn-block" onClick={submit} disabled={state.sending || !form.email || !form.message}>{state.sending ? "Sending…" : "Send message"}</button>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
function Line({ k, v }) { return (<div className="mb-2"><div style={{ fontFamily: "var(--head)", fontWeight: 700, color: "var(--navy)" }}>{k}</div><div className="muted">{v}</div></div>); }
