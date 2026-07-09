import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { PublicLayout, Spinner, money, Badge } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function JobDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const [job, setJob] = useState(null);
  const [msg, setMsg] = useState(null);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    api.get(`/public/jobs/${id}`, { auth: false }).then(r => setJob(r.data)).catch(() => setJob(false));
  }, [id]);

  const apply = async () => {
    if (!user) return nav(`/login?next=/jobs/${id}`);
    if (user.role !== "candidate") { setMsg({ t: "error", m: "Only candidate accounts can apply." }); return; }
    setApplying(true); setMsg(null);
    try {
      await api.post(`/candidate/jobs/${id}/apply`, {});
      setMsg({ t: "ok", m: "Application submitted. Track it from your dashboard." });
    } catch (e) {
      setMsg({ t: "error", m: e.message });
    } finally { setApplying(false); }
  };

  if (job === null) return <PublicLayout><div className="section"><Spinner /></div></PublicLayout>;
  if (job === false) return <PublicLayout><div className="section container empty"><div className="big">Position not found</div><Link to="/jobs" className="btn btn-ghost mt-2">← Back to jobs</Link></div></PublicLayout>;

  const req = job.requirement || {};
  return (
    <PublicLayout>
      <section className="section-sm" style={{ background: "var(--grey)" }}>
        <div className="container">
          <Link to="/jobs" className="muted" style={{ fontSize: ".9rem" }}>← All jobs</Link>
          <div className="flex between wrap gap mt-2" style={{ alignItems: "flex-start" }}>
            <div>
              <span className="badge badge-blue">{job.program_type_name || "Program"}</span>
              <h1 className="mt-2" style={{ fontFamily: "var(--display)", fontSize: "2.2rem" }}>{job.title}</h1>
              <div className="job meta mt-1">
                <span>📍 {job.work_city || "—"}{job.prefecture_name ? `, ${job.prefecture_name}` : ""}</span>
                <span>🏭 {job.job_sector_name || "—"}</span>
                <span>👥 {job.number_of_positions} openings</span>
              </div>
            </div>
            <div className="card card-pad" style={{ minWidth: 260 }}>
              <div className="muted" style={{ fontSize: ".8rem", textTransform: "uppercase", letterSpacing: ".05em" }}>Monthly salary</div>
              <div style={{ fontFamily: "var(--display)", fontWeight: 800, fontSize: "1.6rem", color: "var(--red)" }}>{money(job.salary_min, job.salary_max, job.salary_currency, job.salary_type)}</div>
              <button className="btn btn-primary btn-block mt-2" onClick={apply} disabled={applying}>{applying ? "Submitting…" : "Apply now"}</button>
              {msg && <div className={`alert ${msg.t === "ok" ? "alert-ok" : "alert-error"} mt-2 mb-0`}>{msg.m}</div>}
            </div>
          </div>
        </div>
      </section>

      <section className="section-sm">
        <div className="container grid cols-2" style={{ alignItems: "start" }}>
          <div>
            <h3 style={{ fontSize: "1.2rem", marginBottom: ".6rem" }}>About this role</h3>
            <p className="muted" style={{ whiteSpace: "pre-line" }}>{job.description || "Details will be provided during the interview process."}</p>
            <div className="grid cols-2 mt-3" style={{ gap: 12 }}>
              <Detail k="Working hours" v={job.working_hours} />
              <Detail k="Accommodation" v={job.accommodation_available ? "Available" : "Not provided"} />
              <Detail k="Food support" v={job.food_support} />
              <Detail k="Contract" v={job.contract_period} />
            </div>
          </div>
          <div className="card card-pad">
            <h3 style={{ fontSize: "1.1rem", marginBottom: ".8rem" }}>Requirements</h3>
            <Detail k="Age" v={req.minimum_age ? `${req.minimum_age}–${req.maximum_age || "—"} yrs` : "Any"} />
            <Detail k="Japanese level" v={req.japanese_level || "Not specified"} />
            <Detail k="Skill test" v={req.skill_test_required ? "Required" : "Not required"} />
            <Detail k="Gender preference" v={req.gender_preference || "Any"} />
            <Detail k="Education" v={req.education_requirement || "As per role"} />
            <div className="privacy-note mt-3" style={{ marginBottom: 0 }}>🔒 Applications are managed by JapanCareer.jp. Employers never receive your contact details directly.</div>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
function Detail({ k, v }) {
  return (<div><div className="muted" style={{ fontSize: ".78rem", textTransform: "uppercase", letterSpacing: ".04em" }}>{k}</div><div style={{ fontWeight: 600 }}>{v || "—"}</div></div>);
}
