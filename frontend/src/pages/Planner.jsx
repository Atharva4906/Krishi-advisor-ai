import { useEffect, useState } from 'react';
import { api } from '../api';

const empty = { crop_id: '', area_acres: '', sowing_date: '', expected_harvest: '', irrigation_plan: '', soil_type: 'काळी माती / Black', notes: '' };
const emptyExpense = { category: 'बियाणे / Seeds', amount: '', expense_date: '', plan_id: '', notes: '' };
const expenseCategories = ['बियाणे / Seeds', 'खते / Fertilizer', 'मजुरी / Labour', 'सिंचन / Irrigation', 'फवारणी / Crop protection', 'वाहतूक / Transport', 'इतर / Other'];

export default function Planner() {
  const [crops, setCrops] = useState([]);
  const [plans, setPlans] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [totalExpenses, setTotalExpenses] = useState(0);
  const [form, setForm] = useState(empty);
  const [expenseForm, setExpenseForm] = useState(emptyExpense);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [message, setMessage] = useState('');
  const load = () => Promise.all([api('/api/crops'), api('/api/planner'), api('/api/planner/expenses')]).then(([cropData, planData, expenseData]) => {
    setCrops(cropData); setPlans(planData); setExpenses(expenseData.expenses); setTotalExpenses(expenseData.total);
  }).catch((err) => setMessage(err.message));
  useEffect(load, []);
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const updateExpense = (event) => setExpenseForm({ ...expenseForm, [event.target.name]: event.target.value });
  async function submit(event) {
    event.preventDefault();
    if (form.expected_harvest && form.sowing_date && form.expected_harvest < form.sowing_date) {
      setMessage('कापणीची तारीख पेरणीच्या तारखेनंतर असावी.'); return;
    }
    try { await api('/api/planner', { method: 'POST', body: JSON.stringify(form) }); setForm(empty); setMessage('पीक नियोजन जतन झाले.'); load(); } catch (err) { setMessage(err.message); }
  }
  async function submitExpense(event) {
    event.preventDefault();
    try { await api('/api/planner/expenses', { method: 'POST', body: JSON.stringify(expenseForm) }); setExpenseForm(emptyExpense); setMessage('खर्च नोंदवला.'); load(); } catch (err) { setMessage(err.message); }
  }
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const daysUntil = (date) => {
    if (!date) return null;
    return Math.ceil((new Date(`${date}T00:00:00`) - today) / 86400000);
  };
  const visiblePlans = plans.filter((plan) => {
    const matchesQuery = `${plan.name_mr || ''} ${plan.name_en || ''}`.toLowerCase().includes(query.toLowerCase());
    const days = daysUntil(plan.expected_harvest);
    const matchesFilter = filter === 'all' || (filter === 'upcoming' && days !== null && days >= 0 && days <= 30) || (filter === 'overdue' && days !== null && days < 0);
    return matchesQuery && matchesFilter;
  });
  const upcoming = plans.filter((plan) => { const days = daysUntil(plan.expected_harvest); return days !== null && days >= 0 && days <= 14; });
  const totalArea = plans.reduce((sum, plan) => sum + Number(plan.area_acres || 0), 0);
  const expenseByCategory = expenses.reduce((result, expense) => ({ ...result, [expense.category]: (result[expense.category] || 0) + Number(expense.amount || 0) }), {});
  return <section>
    <div className="page-heading"><p className="eyebrow">Farm Planner</p><h1>शेती नियोजन</h1><p>पिकाची तारीख, क्षेत्र, माती, सिंचन आणि खर्च एका ठिकाणी जतन करा.</p></div>
    <div className="stats planner-stats"><div className="card"><small>एकूण नियोजित क्षेत्र</small><strong>{totalArea.toFixed(1)} acre</strong></div><div className="card"><small>पीक नियोजने</small><strong>{plans.length}</strong></div><div className="card"><small>एकूण शेती खर्च</small><strong>₹{Number(totalExpenses).toLocaleString('en-IN')}</strong></div><div className="card"><small>लवकर कापणी</small><strong>{upcoming.length}</strong></div></div>
    {upcoming.length > 0 && <div className="planner-alert"><strong>पुढील १४ दिवसांची कामे:</strong> {upcoming.map((plan) => `${plan.name_mr || plan.name_en} (${daysUntil(plan.expected_harvest)} दिवस)`).join(' · ')}</div>}
    <div className="grid two">
      <form className="card form" onSubmit={submit}><h2>नवीन पीक नियोजन</h2><label>पीक<select name="crop_id" value={form.crop_id} onChange={update} required><option value="">पीक निवडा</option>{crops.map((crop) => <option key={crop.id} value={crop.id}>{crop.name_mr || crop.name_en}</option>)}</select></label><label>क्षेत्र (acres)<input name="area_acres" type="number" min=".1" step=".1" value={form.area_acres} onChange={update} required /></label><label>मातीचा प्रकार<select name="soil_type" value={form.soil_type} onChange={update}><option>काळी माती / Black</option><option>लाल माती / Red</option><option>गाळाची माती / Alluvial</option><option>इतर / Other</option></select></label><label>पेरणी तारीख<input name="sowing_date" type="date" value={form.sowing_date} onChange={update} /></label><label>अपेक्षित कापणी<input name="expected_harvest" type="date" value={form.expected_harvest} onChange={update} /></label><label>सिंचन योजना<textarea name="irrigation_plan" value={form.irrigation_plan} onChange={update} placeholder="उदा. ठिबक – दर ३ दिवसांनी" /></label><label>कामांची यादी / नोट्स<textarea name="notes" value={form.notes} onChange={update} /></label><button className="button primary">नियोजन जतन करा</button>{message && <p>{message}</p>}</form>
      <form className="card form" onSubmit={submitExpense}><h2>खर्च नोंदवा</h2><label>खर्चाचा प्रकार<select name="category" value={expenseForm.category} onChange={updateExpense}>{expenseCategories.map((category) => <option key={category}>{category}</option>)}</select></label><label>रक्कम (₹)<input name="amount" type="number" min="1" step=".01" value={expenseForm.amount} onChange={updateExpense} required /></label><label>तारीख<input name="expense_date" type="date" value={expenseForm.expense_date} onChange={updateExpense} /></label><label>पीक नियोजन<select name="plan_id" value={expenseForm.plan_id} onChange={updateExpense}><option value="">सर्वसाधारण खर्च</option>{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name_mr || plan.name_en} – {plan.area_acres} acre</option>)}</select></label><label>नोट्स<input name="notes" value={expenseForm.notes} onChange={updateExpense} /></label><button className="button primary">खर्च जतन करा</button></form>
    </div>
    <div className="card planner-list"><div className="planner-toolbar"><h2>तुमची पीक नियोजने</h2><input aria-label="पीक शोधा" placeholder="पीक शोधा..." value={query} onChange={(event) => setQuery(event.target.value)} /><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">सर्व नियोजने</option><option value="upcoming">पुढील ३० दिवस</option><option value="overdue">उशीर झालेली</option></select></div>{visiblePlans.length ? visiblePlans.map((plan) => { const days = daysUntil(plan.expected_harvest); return <article className="plan-row" key={plan.id}><strong>{plan.name_mr || plan.name_en}</strong><span>{plan.area_acres} acre · {plan.soil_type || 'माती नमूद नाही'} · {plan.expected_harvest || 'कापणी तारीख नाही'}</span><small>{days === null ? 'कापणी तारीख ठरवलेली नाही' : days < 0 ? `${Math.abs(days)} दिवस उशीर` : days === 0 ? 'आज कापणी' : `${days} दिवसांत कापणी`} · {plan.irrigation_plan || 'सिंचन योजना नाही'}</small></article>; }) : <p>या फिल्टरसाठी नियोजन सापडले नाही.</p>}</div>
    <div className="card"><h2>खर्चाचा आढावा</h2>{Object.keys(expenseByCategory).length ? <div className="expense-summary">{Object.entries(expenseByCategory).map(([category, amount]) => <div key={category}><span>{category}</span><strong>₹{amount.toLocaleString('en-IN')}</strong></div>)}</div> : <p>अजून खर्च नोंदवलेला नाही.</p>}</div>
  </section>;
}
