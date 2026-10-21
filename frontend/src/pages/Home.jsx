import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <section className="hero">
      <div>
        <p className="eyebrow">Maharashtra Farmer Decision Support</p>
        <h1>शेतकऱ्यांसाठी स्मार्ट <span>AI सल्ला</span></h1>
        <p className="lead">
          पिकाचा भाव, साठवणूक, विक्रीची योग्य वेळ आणि नफा याबद्दल
          डेटावर आधारित निर्णय घ्या.
        </p>
        <div className="actions">
          <Link className="button primary" to="/advisor">AI सल्ला घ्या</Link>
          <a className="button secondary" href="http://127.0.0.1:5000/register">मोफत नोंदणी</a>
        </div>
      </div>
      <div className="hero-card">
        <strong>या React app मध्ये</strong>
        <ul>
          <li>Flask AI prediction API जोडलेले आहे</li>
          <li>Existing Jinja frontend सुरक्षित आहे</li>
          <li>Dashboard API मधून live farmer data येतो</li>
        </ul>
      </div>
    </section>
  );
}
