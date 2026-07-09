import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { api } from "../api";
import { Spinner, Badge, money } from "../components/ui";
import { useAuth } from "../context/AuthContext";

const NAV = [
  { key: "overview", label: "Overview", icon: "▚" },
  { key: "applications", label: "My Applications", icon: "✎" },
  { key: "interviews", label: "Interviews", icon: "☷" },
  { key: "jobs", label: "Find Jobs", icon: "⌕" },
  { key: "notifications", label: "Notifications", icon: "◔" },
];

export default function CandidateDash() {
  const { user, refreshMe } = useAuth();
  const [tab, setTab] = useState("overview");
  return (
    <DashLayout title="Candidate" nav={NAV} active={tab} onNav={setTab}>
      {tab === "overview" && <Overview user={user} onRefresh={refreshMe} />}
      {tab === "applications" && <Applications />}
      {tab === "interviews" && <Interviews />}
      {tab === "jobs" && <FindJobs />}
      {tab === "notifications" && <Notifications />}
    </DashLayout>
  );
}

function Overview({ user, onRefresh }) {
  const [comp, setComp] = useState(null);
  const [msg, setMsg] = useState(null);
  const p = user?.profile || {};
  useEffect(() => { api.get("/candidate/profile/completion").then(r => setComp(r.data)).catch(() => setComp(false)); }, []);
  const submit = async () => {
    setMsg(null);
    try { await api.post("/candidate/profile/submit", {}); setMsg({ t: "ok", m: "Profile submitted for verification." }); onRefresh(); }
    catch (e) { setMsg({ t: "error", m: e.message }); }
  };
  const pct = comp?.profile_completion_percentage ?? p.profile_completion_percentage ?? 0;
  return (
    <>
      {msg && <div className={`alert ${msg.t === "ok" ? "alert-ok" : "alert-error"}`}>{msg.m}</div>}
      <div className="grid cols-3 mb-3">
        <div className="kpi accent"><div className="l">Candidate code</div><div className="n" style={{ fontSize: "1.3rem" }}>{p.candidate_code || "—"}</div></div>
        <div className="kpi"><div className="l">Verification</div><div className="mt-1"><Badge status={p.verification_status}>{p.verification_status}</Badge></div></div>
        <div className="kpi"><div className="l">Current status</div><div className="mt-1"><Badge status={p.current_status}>{p.current_status}</Badge></div></div>
      </div>
      <div className="card card-pad">
        <div className="flex between items-center wrap gap">
          <div>
            <h3 style={{ fontSize: "1.1rem" }}>Profile completion</h3>
            <p className="muted mb-0">Complete your profile to become eligible for verification and job applications.</p>
          </div>
          <div style={{ fontFamily: "var(--display)", fontWeight: 800, fontSize: "2rem", color: pct >= 60 ? "var(--green)" : "var(--orange)" }}>{pct}%</div>
        </div>
        <div style={{ height: 10, background: "var(--grey-2)", borderRadius: 999, marginTop: 14, overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: pct >= 60 ? "var(--green)" : "var(--orange)", transition: ".4s" }} />
        </div>
        {comp?.missing_sections?.length > 0 && (
          <div className="mt-3"><div className="muted mb-2" style={{ fontSize: ".85rem" }}>Still needed:</div>
            <div className="pill-row">{comp.missing_sections.map(s => <span key={s} className="badge badge-orange">{s.replace(/_/g, " ")}</span>)}</div>
          </div>
        )}
        {p.verification_status !== "verified" && (
          <button className="btn btn-primary mt-3" disabled={pct < 60} onClick={submit}>
            {pct < 60 ? "Reach 60% to submit" : "Submit for verification"}
          </button>
        )}
      </div>
    </>
  );
}

function Applications() {
  const [apps, setApps] = useState(null);
  const load = () => api.get("/candidate/applications").then(r => setApps(r.data || [])).catch(() => setApps([]));
  useEffect(() => { load(); }, []);
  const withdraw = async (id) => { try { await api.post(`/candidate/applications/${id}/withdraw`, {}); load(); } catch { /* */ } };
  if (!apps) return <Spinner />;
  if (!apps.length) return <Empty title="No applications yet" sub="Browse open jobs and apply — your applications will appear here." />;
  return (
    <table className="table">
      <thead><tr><th>Job</th><th>Applied</th><th>Status</th><th></th></tr></thead>
      <tbody>{apps.map(a => (
        <tr key={a.id}>
          <td style={{ fontWeight: 600 }}>{a.job_title || a.job?.title || `Job #${a.job}`}</td>
          <td className="muted">{fmt(a.created_at)}</td>
          <td><Badge status={a.status}>{a.status}</Badge></td>
          <td>{["submitted", "under_review", "pending"].includes(a.status) && <button className="btn btn-ghost btn-sm" onClick={() => withdraw(a.id)}>Withdraw</button>}</td>
        </tr>
      ))}</tbody>
    </table>
  );
}

function Interviews() {
  const [items, setItems] = useState(null);
  const load = () => api.get("/candidate/interviews").then(r => setItems(r.data || [])).catch(() => setItems([]));
  useEffect(() => { load(); }, []);
  const confirm = async (id) => { try { await api.post(`/candidate/interviews/${id}/confirm`, {}); load(); } catch { /* */ } };
  if (!items) return <Spinner />;
  if (!items.length) return <Empty title="No interviews scheduled" sub="When our team schedules an interview for you, it will show up here." />;
  return (
    <div className="grid cols-2">{items.map(i => (
      <div className="card card-pad" key={i.id}>
        <div className="flex between items-center"><span className="badge badge-blue">{i.interview_code}</span><Badge status={i.interview_status || i.status}>{i.interview_status || i.status}</Badge></div>
        <h3 className="mt-2" style={{ fontSize: "1.05rem" }}>{i.job_title || "Interview"}</h3>
        <p className="muted mb-2">📅 {i.interview_date} · {i.start_time}{i.meeting_platform ? ` · ${i.meeting_platform}` : ""}</p>
        {i.meeting_url && <a className="btn btn-ghost btn-sm" href={i.meeting_url} target="_blank" rel="noreferrer">Join link</a>}
        {!i.candidate_confirmed && <button className="btn btn-primary btn-sm mt-2" onClick={() => confirm(i.id)}>Confirm attendance</button>}
      </div>
    ))}</div>
  );
}

function FindJobs() {
  const [jobs, setJobs] = useState(null);
  const [msg, setMsg] = useState(null);
  useEffect(() => { api.get("/candidate/jobs").then(r => setJobs(r.data || [])).catch(() => setJobs([])); }, []);
  const apply = async (id) => { setMsg(null); try { await api.post(`/candidate/jobs/${id}/apply`, {}); setMsg({ t: "ok", m: "Applied! Check My Applications." }); } catch (e) { setMsg({ t: "error", m: e.message }); } };
  if (!jobs) return <Spinner />;
  return (<>
    {msg && <div className={`alert ${msg.t === "ok" ? "alert-ok" : "alert-error"}`}>{msg.m}</div>}
    {!jobs.length ? <Empty title="No open jobs right now" sub="Check back soon — new roles are posted regularly." /> : (
      <div className="grid cols-3">{jobs.map(j => (
        <div className="card card-pad job" key={j.id}>
          <span className="badge badge-blue">{j.program_type_name || "Program"}</span>
          <div className="title">{j.title}</div>
          <div className="meta"><span>📍 {j.work_city || "Japan"}</span></div>
          <div className="salary">{money(j.salary_min, j.salary_max, j.salary_currency, j.salary_type)}</div>
          <button className="btn btn-primary btn-sm mt-1" onClick={() => apply(j.id)}>Apply</button>
        </div>
      ))}</div>
    )}
  </>);
}

function Notifications() {
  const [items, setItems] = useState(null);
  const load = () => api.get("/candidate/notifications").then(r => setItems(r.data || [])).catch(() => setItems([]));
  useEffect(() => { load(); }, []);
  const readAll = async () => { try { await api.post("/candidate/notifications/read-all", {}); load(); } catch { /* */ } };
  if (!items) return <Spinner />;
  if (!items.length) return <Empty title="You're all caught up" sub="Notifications about your verification, applications, and interviews appear here." />;
  return (<>
    <div className="flex between items-center mb-2"><span className="muted">{items.filter(i => !i.is_read).length} unread</span><button className="btn btn-ghost btn-sm" onClick={readAll}>Mark all read</button></div>
    {items.map(n => (
      <div className="card card-pad mb-2" key={n.id} style={{ borderLeft: `3px solid ${n.is_read ? "var(--line)" : "var(--red)"}` }}>
        <div className="flex between"><strong style={{ fontFamily: "var(--head)" }}>{n.title}</strong><span className="muted" style={{ fontSize: ".8rem" }}>{fmt(n.created_at)}</span></div>
        <p className="muted mb-0 mt-1">{n.message}</p>
      </div>
    ))}
  </>);
}

function Empty({ title, sub }) { return <div className="empty"><div className="big">{title}</div><p>{sub}</p></div>; }
function fmt(d) { return d ? new Date(d).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "—"; }
