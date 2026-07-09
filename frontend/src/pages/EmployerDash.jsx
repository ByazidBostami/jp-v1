import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { api } from "../api";
import { Spinner, Badge, Field, money } from "../components/ui";
import { useAuth } from "../context/AuthContext";

const NAV = [
  { key: "overview", label: "Overview", icon: "▚" },
  { key: "search", label: "Search Talent", icon: "⌕" },
  { key: "jobs", label: "My Jobs", icon: "≣" },
  { key: "shortlist", label: "Shortlist", icon: "★" },
  { key: "interviews", label: "Interviews", icon: "☷" },
];

export default function EmployerDash() {
  const { user } = useAuth();
  const [tab, setTab] = useState("overview");
  return (
    <DashLayout title="Employer" nav={NAV} active={tab} onNav={setTab}>
      {tab === "overview" && <Overview user={user} />}
      {tab === "search" && <Search />}
      {tab === "jobs" && <Jobs />}
      {tab === "shortlist" && <Shortlist />}
      {tab === "interviews" && <Interviews />}
    </DashLayout>
  );
}

function Overview({ user }) {
  const [st, setSt] = useState(null);
  const [profile, setProfile] = useState(null);
  useEffect(() => {
    api.get("/employer/approval-status").then(r => setSt(r.data)).catch(() => setSt(false));
    api.get("/employer/profile").then(r => setProfile(r.data)).catch(() => {});
  }, []);
  const status = st?.approval_status || "pending";
  const company = profile?.company_name_english || user?.profile?.company_name_english || "—";
  return (
    <>
      {status !== "approved" && (
        <div className="alert alert-info">Your employer account is <strong>{status}</strong>. Talent search and interview requests unlock once an administrator approves your company.</div>
      )}
      <div className="grid cols-3">
        <div className="kpi accent"><div className="l">Company</div><div className="n" style={{ fontSize: "1.2rem" }}>{company}</div></div>
        <div className="kpi"><div className="l">Approval status</div><div className="mt-1"><Badge status={status}>{status}</Badge></div></div>
        <div className="kpi"><div className="l">Talent search</div><div className="mt-1"><Badge status={status === "approved" ? "active" : "pending"}>{status === "approved" ? "Enabled" : "Locked"}</Badge></div></div>
      </div>
      <div className="card card-pad mt-3">
        <h3 style={{ fontSize: "1.1rem" }}>How hiring works here</h3>
        <p className="muted mb-0">Search admin-verified candidates by skill and program. You'll see qualifications and experience — never personal contact details. Shortlist candidates, then request an interview; our team coordinates scheduling and results on your behalf.</p>
      </div>
    </>
  );
}

function Search() {
  const [ref, setRef] = useState({ job_sectors: [], programs: [] });
  const [f, setF] = useState({ japanese_level: "", job_sector: "", gender: "", skill_test_status: "" });
  const [res, setRes] = useState(null);
  const [detail, setDetail] = useState(null);

  useEffect(() => { api.get("/public/reference", { auth: false }).then(r => setRef(r.data)).catch(() => {}); }, []);
  const run = () => {
    setRes(null);
    const p = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => v && p.set(k, v));
    api.get(`/employer/candidates?${p}`).then(r => setRes(r.data || [])).catch(e => setRes({ error: e.message }));
  };
  useEffect(() => { run(); /* eslint-disable-next-line */ }, []);

  return (
    <>
      <div className="privacy-note">🔒 Search results show verified qualifications only. Names, contact details, and documents are protected by JapanCareer.jp.</div>
      <div className="card card-pad mb-3">
        <div className="grid cols-4" style={{ gap: 12 }}>
          <Field label="Japanese level"><select className="input" value={f.japanese_level} onChange={e => setF({ ...f, japanese_level: e.target.value })}><option value="">Any</option>{["N5", "N4", "N3", "N2", "N1"].map(l => <option key={l}>{l}</option>)}</select></Field>
          <Field label="Sector"><select className="input" value={f.job_sector} onChange={e => setF({ ...f, job_sector: e.target.value })}><option value="">Any</option>{ref.job_sectors.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></Field>
          <Field label="Gender"><select className="input" value={f.gender} onChange={e => setF({ ...f, gender: e.target.value })}><option value="">Any</option><option value="male">Male</option><option value="female">Female</option></select></Field>
          <Field label="Skill test"><select className="input" value={f.skill_test_status} onChange={e => setF({ ...f, skill_test_status: e.target.value })}><option value="">Any</option><option value="passed">Passed</option></select></Field>
        </div>
        <button className="btn btn-primary" onClick={run}>Search candidates</button>
      </div>

      {!res ? <Spinner /> : res.error ? <div className="alert alert-error">{res.error}</div> : res.length === 0 ? (
        <Empty title="No candidates match" sub="Adjust the filters to widen your search." />
      ) : (
        <div className="grid cols-3">{res.map(c => (
          <div className="card card-pad" key={c.candidate_code || c.id}>
            <div className="flex between items-center"><span className="badge badge-green">Verified</span><span className="muted" style={{ fontSize: ".8rem" }}>{c.candidate_code}</span></div>
            <h3 className="mt-2" style={{ fontSize: "1.05rem" }}>{c.age ? `${c.age} yrs` : "Candidate"}{c.gender ? ` · ${c.gender}` : ""}</h3>
            <div className="pill-row mt-1">
              {c.highest_japanese_level && <span className="badge badge-blue">JP {c.highest_japanese_level}</span>}
              {c.highest_education && <span className="badge badge-grey">{c.highest_education}</span>}
            </div>
            <p className="muted mt-2 mb-2" style={{ fontSize: ".88rem" }}>📍 {c.general_location || "Bangladesh"}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => api.get(`/employer/candidates/${c.id}`).then(r => setDetail(r.data)).catch(() => {})}>View profile</button>
          </div>
        ))}</div>
      )}

      {detail && <DetailModal c={detail} onClose={() => setDetail(null)} />}
    </>
  );
}

function DetailModal({ c, onClose }) {
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(20,32,60,.55)", display: "flex", alignItems: "center", justifyContent: "center", padding: 20, zIndex: 100 }}>
      <div className="card card-pad" onClick={e => e.stopPropagation()} style={{ maxWidth: 560, width: "100%", maxHeight: "85vh", overflow: "auto" }}>
        <div className="flex between items-center mb-2"><span className="badge badge-green">Verified · {c.candidate_code}</span><button className="btn btn-ghost btn-sm" onClick={onClose}>Close</button></div>
        <div className="privacy-note">🔒 Contact details are withheld. To proceed, add to shortlist and request an interview.</div>
        <div className="grid cols-2" style={{ gap: 10 }}>
          <KV k="Age" v={c.age && `${c.age} yrs`} /><KV k="Gender" v={c.gender} />
          <KV k="Japanese level" v={c.highest_japanese_level} /><KV k="Education" v={c.highest_education} />
          <KV k="Location" v={c.general_location} /><KV k="Availability" v={c.availability_status} />
        </div>
        {Array.isArray(c.skills) && c.skills.length > 0 && <><div className="divider" /><h4 style={{ fontSize: ".9rem" }}>Skills & tests</h4><div className="pill-row">{c.skills.map(s => <span key={s.id} className="badge badge-green">{s.sector_name || s.test_name} · {s.result_status}</span>)}</div></>}
        {Array.isArray(c.languages) && c.languages.length > 0 && <><h4 className="mt-3" style={{ fontSize: ".9rem" }}>Language</h4><div className="pill-row">{c.languages.map(l => <span key={l.id} className="badge badge-blue">{l.qualification_type_name} {l.level}</span>)}</div></>}
        {c.experience_summary && <><h4 className="mt-3" style={{ fontSize: ".9rem" }}>Experience</h4><p className="muted mb-0">{c.experience_summary}</p></>}
      </div>
    </div>
  );
}
function KV({ k, v }) { return <div><div className="muted" style={{ fontSize: ".76rem", textTransform: "uppercase" }}>{k}</div><div style={{ fontWeight: 600 }}>{v || "—"}</div></div>; }

function Jobs() {
  const [jobs, setJobs] = useState(null);
  const [show, setShow] = useState(false);
  const load = () => api.get("/employer/jobs").then(r => setJobs(r.data || [])).catch(() => setJobs([]));
  useEffect(() => { load(); }, []);
  const submit = async (id) => { try { await api.post(`/employer/jobs/${id}/submit`, {}); load(); } catch { /* */ } };
  if (!jobs) return <Spinner />;
  return (<>
    <div className="flex between items-center mb-3"><p className="muted mb-0">Jobs are reviewed by an administrator before they appear publicly.</p><button className="btn btn-primary btn-sm" onClick={() => setShow(true)}>+ New job</button></div>
    {!jobs.length ? <Empty title="No jobs posted" sub="Create your first job posting to start hiring." /> : (
      <table className="table"><thead><tr><th>Title</th><th>Sector</th><th>Approval</th><th>Status</th><th></th></tr></thead>
        <tbody>{jobs.map(j => (
          <tr key={j.id}><td style={{ fontWeight: 600 }}>{j.title}</td><td className="muted">{j.job_sector_name || "—"}</td>
            <td><Badge status={j.approval_status}>{j.approval_status}</Badge></td><td><Badge status={j.job_status}>{j.job_status}</Badge></td>
            <td>{["draft", "correction_required"].includes(j.approval_status) && <button className="btn btn-ghost btn-sm" onClick={() => submit(j.id)}>Submit</button>}</td>
          </tr>
        ))}</tbody>
      </table>
    )}
    {show && <JobModal onClose={() => setShow(false)} onSaved={() => { setShow(false); load(); }} />}
  </>);
}

function JobModal({ onClose, onSaved }) {
  const [ref, setRef] = useState({ programs: [], job_sectors: [], japan_regions: [] });
  const [f, setF] = useState({ title: "", program_type: "", job_sector: "", work_city: "", number_of_positions: 1, salary_min: "", salary_max: "", description: "" });
  const [err, setErr] = useState(null);
  useEffect(() => { api.get("/public/reference", { auth: false }).then(r => setRef(r.data)).catch(() => {}); }, []);
  const save = async () => {
    setErr(null);
    try { await api.post("/employer/jobs", { ...f, salary_currency: "JPY", salary_type: "monthly" }); onSaved(); }
    catch (e) { setErr(e.errors ? Object.values(e.errors).flat().join(" ") : e.message); }
  };
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(20,32,60,.55)", display: "flex", alignItems: "center", justifyContent: "center", padding: 20, zIndex: 100 }}>
      <div className="card card-pad" onClick={e => e.stopPropagation()} style={{ maxWidth: 620, width: "100%", maxHeight: "88vh", overflow: "auto" }}>
        <h3 className="mb-2">New job posting</h3>
        {err && <div className="alert alert-error">{err}</div>}
        <Field label="Job title"><input className="input" value={f.title} onChange={e => setF({ ...f, title: e.target.value })} /></Field>
        <div className="grid cols-2" style={{ gap: 12 }}>
          <Field label="Program"><select className="input" value={f.program_type} onChange={e => setF({ ...f, program_type: e.target.value })}><option value="">Select</option>{ref.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
          <Field label="Sector"><select className="input" value={f.job_sector} onChange={e => setF({ ...f, job_sector: e.target.value })}><option value="">Select</option>{ref.job_sectors.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></Field>
        </div>
        <div className="grid cols-3" style={{ gap: 12 }}>
          <Field label="City"><input className="input" value={f.work_city} onChange={e => setF({ ...f, work_city: e.target.value })} /></Field>
          <Field label="Openings"><input className="input" type="number" min="1" value={f.number_of_positions} onChange={e => setF({ ...f, number_of_positions: e.target.value })} /></Field>
          <Field label="Salary min (¥)"><input className="input" type="number" value={f.salary_min} onChange={e => setF({ ...f, salary_min: e.target.value })} /></Field>
        </div>
        <Field label="Description"><textarea className="input" rows={4} value={f.description} onChange={e => setF({ ...f, description: e.target.value })} /></Field>
        <div className="flex gap-sm"><button className="btn btn-primary" onClick={save}>Save draft</button><button className="btn btn-ghost" onClick={onClose}>Cancel</button></div>
      </div>
    </div>
  );
}

function Shortlist() {
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/employer/shortlists").then(r => setItems(r.data || [])).catch(() => setItems([])); }, []);
  if (!items) return <Spinner />;
  if (!items.length) return <Empty title="Your shortlist is empty" sub="Shortlist candidates from Search Talent to line them up for interviews." />;
  return <div className="grid cols-3">{items.map(s => (
    <div className="card card-pad" key={s.id}><span className="badge badge-green">{s.candidate_code || "Candidate"}</span><p className="muted mt-2 mb-0">{s.notes || "Shortlisted candidate"}</p></div>
  ))}</div>;
}

function Interviews() {
  const [reqs, setReqs] = useState(null);
  useEffect(() => { api.get("/employer/interview-requests").then(r => setReqs(r.data || [])).catch(() => setReqs([])); }, []);
  if (!reqs) return <Spinner />;
  if (!reqs.length) return <Empty title="No interview requests" sub="Once you request interviews for shortlisted candidates, they'll appear here for admin scheduling." />;
  return <table className="table"><thead><tr><th>Request</th><th>Candidates</th><th>Requested</th><th>Status</th></tr></thead>
    <tbody>{reqs.map(r => (<tr key={r.id}><td style={{ fontWeight: 600 }}>{r.request_code}</td><td>{r.candidate_count ?? (r.candidates?.length || "—")}</td><td className="muted">{r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}</td><td><Badge status={r.request_status}>{r.request_status}</Badge></td></tr>))}</tbody>
  </table>;
}

function Empty({ title, sub }) { return <div className="empty"><div className="big">{title}</div><p>{sub}</p></div>; }
