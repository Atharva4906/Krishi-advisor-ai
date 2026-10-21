import { NavLink, Route, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Advisor from './pages/Advisor';
import Dashboard from './pages/Dashboard';
import Planner from './pages/Planner';
import Stock from './pages/Stock';
import Sales from './pages/Sales';
import Profile from './pages/Profile';

function Layout({ children }) {
  return (
    <>
      <header className="topbar">
        <NavLink className="brand" to="/">Krishi<span>Advisor</span> AI</NavLink>
        <nav>
          <NavLink to="/">मुख्यपृष्ठ</NavLink>
          <NavLink to="/advisor">AI सल्लागार</NavLink>
          <NavLink to="/dashboard">डॅशबोर्ड</NavLink>
          <NavLink to="/planner">शेती नियोजन</NavLink>
          <NavLink to="/stock">साठा</NavLink>
          <NavLink to="/sales">विक्री</NavLink>
          <NavLink to="/profile">प्रोफाइल</NavLink>
          <a href="http://127.0.0.1:5000/login">Existing Flask Login</a>
        </nav>
      </header>
      <main className="container">{children}</main>
    </>
  );
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/advisor" element={<Advisor />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/planner" element={<Planner />} />
        <Route path="/stock" element={<Stock />} />
        <Route path="/sales" element={<Sales />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Layout>
  );
}
