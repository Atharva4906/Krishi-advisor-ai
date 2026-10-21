import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Sales() {
  const [sales, setSales] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { api('/api/sales').then(setSales).catch((err) => setError(`${err.message}. Login through Flask first.`)); }, []);
  return <section><div className="page-heading"><p className="eyebrow">Sales History</p><h1>विक्री इतिहास</h1></div>{error ? <div className="card error">{error}</div> : <div className="card table-wrap"><table><thead><tr><th>पीक</th><th>प्रमाण</th><th>भाव</th><th>एकूण</th><th>नफा</th><th>तारीख</th></tr></thead><tbody>{sales.length ? sales.map((sale) => <tr key={sale.id}><td>{sale.name_mr || sale.name_en}</td><td>{sale.quantity_kg} kg</td><td>₹{sale.sale_price}</td><td>₹{Number(sale.total_amount).toLocaleString('en-IN')}</td><td>₹{Number(sale.profit).toLocaleString('en-IN')}</td><td>{sale.sale_date}</td></tr>) : <tr><td colSpan="6">अजून विक्री नोंदवलेली नाही.</td></tr>}</tbody></table></div>}</section>;
}
