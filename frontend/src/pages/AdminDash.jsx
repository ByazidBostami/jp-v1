import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { api } from "../api";
import { Spinner, Badge } from "../components/ui";

const NAV = [
  { key: "overview", label: "Dashboard", icon: "▚" },
  { key: "candidates", label: "Candidates", icon: "☺" },
  { key: "employers", label: "Employers", icon: "▤" },
  { key: "jobs", label: "Jobs", icon: "≣" },
  { key: "interviews", label: "Interviews", icon: "☷" },
];

export default function AdminDash() {
  const [tab, setTab] = useState("overview");
  return (
    <DashLayout title="Admin Console" nav={NAV} active={tab} onNav={setTab}
      actions={tab === "candidates" && <a className="btn btn-ghost btn-sm" href="/api/v1/admin/reports/candidates?format=csv" onClick={exportCsv}>⭳ Export CSV</a>}>
      {tab === "overview" && <Overview />}
      {tab === "candidates" && <Candidates />}
      {tab === "employers" && <Employers />}
      {tab === "jobs" && <Jobs />}
      {tab === "interviews" && <Interviews />}
    </DashLayout>
  );
}

async function exportCsv(e) {
  e.preventDefault();
  try {
    const token = localStorage.getItem("jc_access");
    const res = await fetch("/api/v1/admin/reports/candidates?format=csv", { headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "candidates.csv"; a.click();
    URL.revokeObjectURL(url);
  } catch { /* */ }
}

function Overview() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/admin/dashboard/summary").then(r => setD(r.data)).catch(() => setD(false)); }, []);
  if (!d) return <Spinner />;
  const cards = [
    ["New today", d.new_candidates_today, true], ["Total candidates", d.total_candidates],
    ["Pending verification", d.pending_verification], ["Verified", d.verified_candidates],
    ["Employers", d.total_employers], ["Pending employers", d.pending_employers],
    ["Active jobs", d.active_jobs], ["Upcoming interviews", d.upcoming_interviews],
    ["Selected", d.selected_candidates], ["Visa processing", d.visa_processing],
    ["Deployed", d.deployed], ["Pending jobs", d.pending_jobs],
  ];
  return (
    <div className="grid cols-4">
      {cards.map(([l, n, accent], i) => (
        <div className={`kpi ${accent ? "accent" : ""}`} key={i}><div className="n">{n ?? 0}</div><div className="l">{l}</div></div>
      ))}
    </div>
  );
}

function useList(path) {
  const [data, setData] = useState(null);
  const load = () => api.get(path).then(r => setData(r.data || [])).catch(() => setData([]));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [path]);
  return [data, load];
}

function Candidates() {
  const [filter, setFilter] = useState("pending_verification");
  const [rows, load] = useList(`/admin/candidates?verification_status=${filter}`);
  const act = async (id, action, body = {}) => { try { await api.post(`/admin/candidates/${id}/${action}`, body); load(); } catch { /* */ } };
  return (<>
    <div className="pill-row mb-3">
      {["pending_verification", "verified", "new", "rejected", ""].map(s => (
        <button key={s || "all"} className={`btn btn-sm ${filter === s ? "btn-navy" : "btn-ghost"}`} onClick={() => setFilter(s)}>{s ? s.replace(/_/g, " ") : "all"}</button>
      ))}
    </div>
    {!rows ? <Spinner /> : !rows.length ? <div className="empty"><div className="big">No candidates</div></div> : (
      <table className="table"><thead><tr><th>Code</th><th>Name</th><th>Nationality</th><th>Verification</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>{rows.map(c => (
          <tr key={c.id}>
            <td className="muted">{c.candidate_code}</td><td style={{ fontWeight: 600 }}>{c.full_name}</td>
            <td>{c.nationality || "—"}</td>
            <td><Badge status={c.verification_status}>{c.verification_status}</Badge></td>
            <td><Badge status={c.current_status}>{c.current_status}</Badge></td>
            <td><div className="row-actions">
              {c.verification_status !== "verified" && <button className="btn btn-primary btn-sm" onClick={() => act(c.id, "approve")}>Approve</button>}
              {c.verification_status !== "rejected" && <button className="btn btn-ghost btn-sm" onClick={() => act(c.id, "reject", { reason: "Did not meet criteria" })}>Reject</button>}
              <button className="btn btn-ghost btn-sm" onClick={() => act(c.id, "request-correction", { reason: "Please update your documents" })}>Request fix</button>
            </div></td>
          </tr>
        ))}</tbody>
      </table>
    )}
  </>);
}

function Employers() {
  const [rows, load] = useList("/admin/employers");
  const act = async (id, action) => { try { await api.post(`/admin/employers/${id}/${action}`, {}); load(); } catch { /* */ } };
  if (!rows) return <Spinner />;
  if (!rows.length) return <div className="empty"><div className="big">No employers</div></div>;
  return <table className="table"><thead><tr><th>Code</th><th>Company</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody>{rows.map(e => (
      <tr key={e.id}><td className="muted">{e.employer_code}</td><td style={{ fontWeight: 600 }}>{e.company_name_english}</td>
        <td><Badge status={e.approval_status}>{e.approval_status}</Badge></td>
        <td><div className="row-actions">
          {e.approval_status !== "approved" && <button className="btn btn-primary btn-sm" onClick={() => act(e.id, "approve")}>Approve</button>}
          {e.approval_status !== "rejected" && <button className="btn btn-ghost btn-sm" onClick={() => act(e.id, "reject")}>Reject</button>}
          {e.approval_status === "approved" && <button className="btn btn-ghost btn-sm" onClick={() => act(e.id, "suspend")}>Suspend</button>}
        </div></td>
      </tr>
    ))}</tbody>
  </table>;
}

function Jobs() {
  const [rows, load] = useList("/admin/jobs");
  const act = async (id, action) => { try { await api.post(`/admin/jobs/${id}/${action}`, {}); load(); } catch { /* */ } };
  if (!rows) return <Spinner />;
  if (!rows.length) return <div className="empty"><div className="big">No jobs</div></div>;
  return <table className="table"><thead><tr><th>Title</th><th>Employer</th><th>Approval</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody>{rows.map(j => (
      <tr key={j.id}><td style={{ fontWeight: 600 }}>{j.title}</td><td className="muted">{j.employer_name || j.company_name || "—"}</td>
        <td><Badge status={j.approval_status}>{j.approval_status}</Badge></td><td><Badge status={j.job_status}>{j.job_status}</Badge></td>
        <td><div className="row-actions">
          {j.approval_status === "pending" && <button className="btn btn-primary btn-sm" onClick={() => act(j.id, "approve")}>Approve</button>}
          {j.approval_status === "approved" && <button className="btn btn-primary btn-sm" onClick={() => act(j.id, "publish")}>Publish</button>}
          {!["rejected"].includes(j.approval_status) && <button className="btn btn-ghost btn-sm" onClick={() => act(j.id, "reject")}>Reject</button>}
        </div></td>
      </tr>
    ))}</tbody>
  </table>;
}

function Interviews() {
  const [rows, load] = useList("/admin/interview-requests");
  const act = async (id, action) => { try { await api.post(`/admin/interview-requests/${id}/${action}`, {}); load(); } catch { /* */ } };
  if (!rows) return <Spinner />;
  if (!rows.length) return <div className="empty"><div className="big">No interview requests</div><p>Employer interview requests will appear here for approval and scheduling.</p></div>;
  return <table className="table"><thead><tr><th>Request</th><th>Employer</th><th>Candidates</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody>{rows.map(r => (
      <tr key={r.id}><td className="muted">{r.request_code}</td><td>{r.employer_name || "—"}</td><td>{r.candidate_count ?? (r.candidates?.length || "—")}</td>
        <td><Badge status={r.request_status}>{r.request_status}</Badge></td>
        <td><div className="row-actions">
          {r.request_status === "pending" && <><button className="btn btn-primary btn-sm" onClick={() => act(r.id, "approve")}>Approve</button><button className="btn btn-ghost btn-sm" onClick={() => act(r.id, "reject")}>Reject</button></>}
        </div></td>
      </tr>
    ))}</tbody>
  </table>;
}
