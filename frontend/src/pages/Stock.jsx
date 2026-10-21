import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Stock() {
  const [stocks, setStocks] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { api('/api/stock').then(setStocks).catch((err) => setError(`${err.message}. Login through Flask first.`)); }, []);
  return <section><div className="page-heading"><p className="eyebrow">Inventory</p><h1>माल साठा</h1><p>तुमच्या शेतातील उपलब्ध साठा पाहा.</p></div>{error ? <div className="card error">{error}</div> : <div className="list">{stocks.length ? stocks.map((stock) => <article className="card stock-row" key={stock.id}><div><h2>{stock.name_mr || stock.name_en}</h2><small>{stock.category} · {stock.storage_type}</small></div><strong>{Number(stock.quantity_kg).toLocaleString('en-IN')} kg</strong><span className={stock.status === 'stored' ? 'status good' : 'status'}>{stock.status}</span></article>) : <div className="card">अजून साठा जोडलेला नाही.</div>}</div>}</section>;
}
