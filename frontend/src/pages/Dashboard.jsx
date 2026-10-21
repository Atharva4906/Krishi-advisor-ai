import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { api('/api/dashboard').then(setData).catch((err) => setError(`${err.message}. Login through the existing Flask app first.`)); }, []);
  if (error) return <div className="card error">{error}</div>;
  if (!data) return <div className="card">Dashboard loading...</div>;
  const { stats, recent_sales: sales, user } = data;
  return <section><div className="page-heading"><p className="eyebrow">Farmer Dashboard</p><h1>नमस्कार, {user.name}</h1></div><div className="stats">{Object.entries({ 'एकूण विक्री': stats.total_sales, 'एकूण नफा': stats.total_profit, 'सक्रिय साठा': stats.active_stock, 'AI सल्ले': stats.prediction_count, 'शेती खर्च': stats.total_expenses }).map(([label, value]) => <div className="card" key={label}><small>{label}</small><strong>{label.includes('साठा') || label.includes('सल्ले') ? value : `₹${Number(value).toLocaleString('en-IN')}`}</strong></div>)}</div><div className="card"><h2>अलीकडील विक्री</h2>{sales.length ? sales.map((sale) => <div className="sale-row" key={sale.id}><span>{sale.name_mr || sale.name_en}</span><span>₹{Number(sale.total_amount).toLocaleString('en-IN')}</span></div>) : <p>अजून विक्री नोंदवलेली नाही.</p>}</div></section>;
}
