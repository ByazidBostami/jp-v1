import { useEffect, useState } from "react";
import { api } from "../api";
import { PublicLayout } from "../components/ui";

export default function About() {
  const [page, setPage] = useState(null);
  useEffect(() => { api.get("/public/pages/about", { auth: false }).then(r => setPage(r.data)).catch(() => setPage(false)); }, []);
  return (
    <PublicLayout>
      <section className="section-sm" style={{ background: "var(--navy)", color: "#fff" }}>
        <div className="container">
          <span className="eyebrow" style={{ color: "#ff9a9a" }}>About</span>
          <h1 className="mt-2" style={{ color: "#fff", fontFamily: "var(--display)", fontSize: "2.4rem" }}>{page?.title || "About JapanCareer.jp"}</h1>
        </div>
      </section>
      <section className="section">
        <div className="container" style={{ maxWidth: 780 }}>
          <p className="lead">{page?.content || "JapanCareer.jp connects Japan-ready candidates from Bangladesh with Japanese employers and education providers through a securely managed, privacy-first platform."}</p>
          <div className="grid cols-3 mt-4">
            {VALUES.map(v => (
              <div className="tile" key={v.t}><div className="k">{v.t}</div><p>{v.d}</p></div>
            ))}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
const VALUES = [
  { t: "Verified & trusted", d: "Every candidate profile and every employer is reviewed and approved by our admin team." },
  { t: "Privacy by design", d: "Candidate contact details and documents are never exposed to employers — the platform mediates all contact." },
  { t: "End-to-end guidance", d: "From profile building through interviews, visa, and COE, we support candidates to departure." },
];
