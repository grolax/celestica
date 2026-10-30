import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import Icon, { IconName } from "@/shared/components/Icon";

const CARDS: [IconName, string, string][] = [
  ["folder", "Importa tus datos", "CSV, Excel, Qualtrics o Google Forms."],
  ["sparkle", "La IA propone, tu equipo decide", "Temas sugeridos que tu equipo valida."],
  ["shield", "Trazabilidad total", "Cada decisión queda registrada."],
  ["file", "Informes listos", "PDF, Word, Excel y CSV."],
];

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const to = isAuthenticated ? "/proyectos" : "/login";
  const label = isAuthenticated ? "Ir a mi espacio" : "Iniciar sesión";

  return (
    <>
      <header className="landing-bar">
        <div className="landing-bar-in">
          <Link to="/" className="logo">
            <span className="logo-mark">C</span>
            <span>Celestica</span>
          </Link>
          <nav className="landing-nav" aria-label="Principal">
            <a href="#nosotros">Quiénes somos</a>
            <a href="#que-hace">Qué hace</a>
            <Link to={to} className="btn btn-primary btn-sm">{label}</Link>
          </nav>
        </div>
      </header>

      <main>
        <section className="landing-sec landing-hero" aria-labelledby="hero-t">
          <div className="landing-in">
            <h1 id="hero-t">De la encuesta al informe en minutos</h1>
            <p>Análisis de encuestas con IA y validación de tu equipo.</p>
            <div className="landing-actions">
              <Link to={to} className="btn btn-primary btn-lg">{label}</Link>
              {!isAuthenticated && <Link to="/signup" className="btn btn-secondary btn-lg">Crear cuenta</Link>}
            </div>
          </div>
        </section>

        <section id="nosotros" className="landing-sec alt">
          <div className="landing-in landing-two">
            <div>
              <h2>Quiénes somos</h2>
              <p>Somos Celestica: análisis social, metodología y tecnología al servicio de las organizaciones que escuchan a su gente.</p>
            </div>
            <div>
              <h2>Nuestro objetivo</h2>
              <p>Que pasar de las respuestas a las decisiones tome minutos, no semanas, con cada objetivo respaldado por evidencia.</p>
            </div>
          </div>
        </section>

        <section id="que-hace" className="landing-sec" aria-labelledby="que-hace-t">
          <div className="landing-in">
            <h2 id="que-hace-t">Qué hace Celestica</h2>
            <div className="landing-cards">
              {CARDS.map(([icon, title, text]) => (
                <div key={title} className="landing-card">
                  <div className="icon-wrap"><Icon name={icon} size={22} /></div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-foot">
        <div className="landing-in">
          <span>Celestica es un producto de SoftInsight · {new Date().getFullYear()}</span>
          <Link to={to}>{label}</Link>
        </div>
      </footer>
    </>
  );
}
