import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { PublicLayout, Spinner, money, Field } from "../components/ui";

export default function Jobs() {
  const [jobs, setJobs] = useState(null);
  const [meta, setMeta] = useState(null);
  const [ref, setRef] = useState({ programs: [], job_sectors: [] });
  const [q, setQ] = useState({ search: "", program_type: "", job_sector: "" });
  const [page, setPage] = useState(1);

  useEffect(() => { api.get("/public/reference", { auth: false }).then(r => setRef(r.data)).catch(() => {}); }, []);

  useEffect(() => {
    setJobs(null);
    const params = new URLSearchParams({ page, per_page: 9 });
    if (q.search) params.set("search", q.search);
    if (q.program_type) params.set("program_type", q.program_type);
    if (q.job_sector) params.set("job_sector", q.job_sector);
    api.get(`/public/jobs?${params}`, { auth: false })
      .then(r => { setJobs(r.data || []); setMeta(r.meta); })
      .catch(() => setJobs([]));
  }, [q, page]);

  return (
    <PublicLayout>
      <section className="section-sm" style={{ background: "var(--navy)", color: "#fff" }}>
        <div className="container">
          <span className="eyebrow" style={{ color: "#ff9a9a" }}>Opportunities in Japan</span>
          <h1 className="mt-2" style={{ color: "#fff", fontFamily: "var(--display)", fontSize: "2.4rem" }}>Browse open positions</h1>
          <p style={{ color: "#c3cbe0", maxWidth: "60ch" }}>Every role is posted by an approved employer and reviewed by our admin team before publication.</p>
        </div>
      </section>

      <section className="section-sm">
        <div className="container">
          <div className="card card-pad mb-3">
            <div className="grid cols-3" style={{ gap: 14 }}>
              <Field label="Search">
                <input className="input" placeholder="Job title or keyword"
                  value={q.search} onChange={e => { setPage(1); setQ({ ...q, search: e.target.value }); }} />
              </Field>
              <Field label="Program">
                <select className="input" value={q.program_type} onChange={e => { setPage(1); setQ({ ...q, program_type: e.target.value }); }}>
                  <option value="">All programs</option>
                  {ref.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </Field>
              <Field label="Sector">
                <select className="input" value={q.job_sector} onChange={e => { setPage(1); setQ({ ...q, job_sector: e.target.value }); }}>
                  <option value="">All sectors</option>
                  {ref.job_sectors.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </Field>
            </div>
          </div>

          {!jobs ? <Spinner /> : jobs.length === 0 ? (
            <div className="empty"><div className="big">No positions match your search</div><p>Try widening your filters or check back soon — new roles are posted regularly.</p></div>
          ) : (
            <>
              <div className="grid cols-3">
                {jobs.map(j => (
                  <Link to={`/jobs/${j.id}`} key={j.id} className="card card-pad job">
                    <div className="flex between items-center">
                      <span className="badge badge-blue">{j.program_type_name || "Program"}</span>
                      {j.job_sector_name && <span className="muted" style={{ fontSize: ".8rem" }}>{j.job_sector_name}</span>}
                    </div>
                    <div className="title">{j.title}</div>
                    <div className="meta">
                      <span>📍 {j.work_city || j.prefecture_name || "Japan"}</span>
                      <span>👥 {j.number_of_positions}</span>
                    </div>
                    <div className="salary">{money(j.salary_min, j.salary_max, j.salary_currency, j.salary_type)}</div>
                  </Link>
                ))}
              </div>
              {meta && meta.last_page > 1 && (
                <div className="flex gap-sm mt-4" style={{ justifyContent: "center" }}>
                  <button className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                  <span className="muted" style={{ alignSelf: "center" }}>Page {meta.current_page} of {meta.last_page}</span>
                  <button className="btn btn-ghost btn-sm" disabled={page >= meta.last_page} onClick={() => setPage(p => p + 1)}>Next →</button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </PublicLayout>
  );
}
