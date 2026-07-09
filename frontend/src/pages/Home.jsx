import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { PublicLayout, Spinner, money } from "../components/ui";

function StatNum({ value }) {
  const big = Number(value) >= 100;
  return <div className="n">{Number(value).toLocaleString()}{big && <span className="plus">+</span>}</div>;
}

export default function Home() {
  const [data, setData] = useState(null);
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    api.get("/public/homepage", { auth: false }).then(r => setData(r.data)).catch(() => setData({ statistics: [], programs: [], job_sectors: [] }));
    api.get("/public/jobs?per_page=3", { auth: false }).then(r => setJobs(r.data || [])).catch(() => {});
  }, []);

  const stats = data?.statistics || [];
  const featured = stats.filter(s => ["total_candidates", "verified_candidates", "registered_employers", "successful_placements"].includes(s.statistic_code));

  return (
    <PublicLayout>
      {/* HERO */}
      <section className="hero">
        <div className="container hero-inner">
          <div>
            <span className="eyebrow">Bangladesh → Japan · Managed placement</span>
            <h1 className="mt-2">Your verified path to a <span className="accent">career in Japan</span></h1>
            <p className="lead">JapanCareer.jp prepares, verifies, and connects skilled candidates from Bangladesh with trusted Japanese employers and education programs — every profile checked, every step guided.</p>
            <div className="hero-cta">
              <Link to="/register" className="btn btn-primary">Create your profile</Link>
              <Link to="/jobs" className="btn btn-ghost">Explore opportunities</Link>
            </div>
            <div className="hero-trust">
              <span><b>Admin-verified</b> candidates</span>
              <span><b>Privacy-first</b> — your contacts stay protected</span>
              <span><b>TITP · SSW · ESD</b> pathways</span>
            </div>
          </div>
          <div className="hero-visual">
            <div className="pathway"><span className="pin" style={{ left: 0 }} /><span className="pin" style={{ right: 0 }} /></div>
            <div className="hinomaru" />
          </div>
        </div>
      </section>

      {/* STAT STRIP */}
      <section className="stat-strip">
        <div className="container">
          {!data ? <Spinner /> : (
            <div className="grid cols-4">
              {(featured.length ? featured : stats.slice(0, 4)).map(s => (
                <div className="stat" key={s.statistic_code}>
                  <StatNum value={s.value} />
                  <div className="l">{s.statistic_label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* PROGRAMS */}
      <section className="section" id="programs">
        <div className="container">
          <span className="eyebrow">Pathways</span>
          <h2 className="mt-2" style={{ fontSize: "2.1rem" }}>Programs built around real Japanese demand</h2>
          <p className="lead mt-2 mb-3">Choose the route that fits your skills and goals. Our team prepares you for each program's specific requirements.</p>
          <div className="grid cols-3">
            {(data?.programs || []).map(p => (
              <div className="tile" key={p.id}>
                <span className="code">{p.code}</span>
                <div className="k">{p.name}</div>
                <p>{PROGRAM_BLURB[p.code] || "A guided pathway toward employment or study in Japan, with full documentation support."}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTORS */}
      <section className="section-sm" style={{ background: "var(--grey)" }}>
        <div className="container">
          <div className="flex between items-center wrap gap mb-3">
            <div>
              <span className="eyebrow">In-demand sectors</span>
              <h2 className="mt-2" style={{ fontSize: "1.8rem" }}>Where our candidates are placed</h2>
            </div>
            <Link to="/jobs" className="btn btn-ghost btn-sm">View open jobs →</Link>
          </div>
          <div className="pill-row">
            {(data?.job_sectors || []).map(s => (
              <span key={s.id} className="badge badge-grey" style={{ fontSize: ".82rem", padding: ".5rem .9rem" }}>{s.name}</span>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURED JOBS */}
      {jobs.length > 0 && (
        <section className="section">
          <div className="container">
            <span className="eyebrow">Latest openings</span>
            <h2 className="mt-2 mb-3" style={{ fontSize: "1.9rem" }}>Featured opportunities</h2>
            <div className="grid cols-3">
              {jobs.map(j => (
                <Link to={`/jobs/${j.id}`} key={j.id} className="card card-pad job">
                  <span className="badge badge-blue">{j.program_type_name || j.program_type?.name || "Program"}</span>
                  <div className="title">{j.title}</div>
                  <div className="meta">
                    <span>📍 {j.work_city || j.prefecture_name || "Japan"}</span>
                    <span>👥 {j.number_of_positions} openings</span>
                  </div>
                  <div className="salary">{money(j.salary_min, j.salary_max, j.salary_currency, j.salary_type)}</div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* HOW IT WORKS */}
      <section className="section" id="how" style={{ background: "var(--grey)" }}>
        <div className="container">
          <span className="eyebrow">How it works</span>
          <h2 className="mt-2 mb-3" style={{ fontSize: "1.9rem" }}>A managed process — start to deployment</h2>
          <div className="grid cols-4">
            {STEPS.map((s, i) => (
              <div className="card card-pad" key={i}>
                <div style={{ fontFamily: "var(--display)", fontWeight: 800, color: "var(--red)", fontSize: "1.5rem" }}>0{i + 1}</div>
                <h3 className="mt-1" style={{ fontSize: "1.05rem" }}>{s.t}</h3>
                <p className="muted mb-0 mt-1" style={{ fontSize: ".9rem" }}>{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section center">
        <div className="container">
          <h2 style={{ fontFamily: "var(--display)", fontSize: "2.3rem" }}>Ready to begin your journey to Japan?</h2>
          <p className="lead mx-auto mt-2 mb-3" style={{ textAlign: "center" }}>Create your profile today. Our team verifies every applicant and guides you through each step.</p>
          <div className="flex gap-sm" style={{ justifyContent: "center" }}>
            <Link to="/register" className="btn btn-primary">Get started free</Link>
            <Link to="/contact" className="btn btn-ghost">Talk to our team</Link>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}

const PROGRAM_BLURB = {
  TITP: "Technical Intern Training Program — build hands-on Japanese work experience across regulated sectors.",
  SSW: "Specified Skilled Worker — for candidates who pass the skills and Japanese-language assessments.",
  ESD: "Employment of Specified Doctors/skilled staff placements matched to employer demand.",
  JLS: "Japanese Language School — study routes with pathways to further work and education.",
  BACHELOR: "Undergraduate study placements at partner institutions in Japan.",
  MASTER: "Graduate study placements for advanced candidates.",
};
const STEPS = [
  { t: "Register & build profile", d: "Create your account and complete your education, language, and skills profile." },
  { t: "Get verified", d: "Our admin team reviews your documents and verifies your qualifications." },
  { t: "Match & interview", d: "Employers discover verified profiles; our team arranges every interview." },
  { t: "Deploy to Japan", d: "From selection through visa and COE, we guide you to departure." },
];
