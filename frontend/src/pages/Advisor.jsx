import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Advisor() {
  const [crops, setCrops] = useState([]);
  const [form, setForm] = useState({ crop_name: '', quantity: 100, current_price: 10, production_cost: 0, transport_cost: 2, storage_cost: 2, temperature: 'medium' });
  const [result, setResult] = useState(null);
  const [aiAdvice, setAiAdvice] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [question, setQuestion] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState('');
  const [questionLoading, setQuestionLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { api('/api/crops').then(setCrops).catch((err) => setError(err.message)); }, []);
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  async function submit(event) {
    event.preventDefault();
    setError('');
    try { setAiAdvice(''); setResult(await api('/api/predict', { method: 'POST', body: JSON.stringify(form) })); }
    catch (err) { setError(err.message); }
  }
  async function askAi() {
    if (!result) return;
    setError('');
    setAiLoading(true);
    try {
      const response = await api('/api/ai-advice', {
        method: 'POST',
        body: JSON.stringify({ ...form, analysis: result }),
      });
      setAiAdvice(response.advice);
    } catch (err) {
      setError(err.message);
    } finally {
      setAiLoading(false);
    }

    async function askFarmQuestion(event) {
      event.preventDefault();
      if (!question.trim()) return;
      setError('');
      setQuestionLoading(true);
      try {
        const response = await api('/api/ai-farm-help', {
          method: 'POST',
          body: JSON.stringify({
            question,
            crop_name: form.crop_name,
            language: 'mr',
            context: result ? {
              quantity_kg: form.quantity,
              current_price: form.current_price,
              strategy: result.best_strategy,
              risk: result.risk,
            } : {},
          }),
        });
        setQuestionAnswer(response.advice);
      } catch (err) {
        setError(err.message);
      } finally {
        setQuestionLoading(false);
      }
    }
  }

  return (
    <section>
      <div className="page-heading"><p className="eyebrow">AI Profit Advisor</p><h1>पिकाचे विश्लेषण करा</h1><p>विक्री, साठवणूक किंवा प्रक्रिया यातील योग्य पर्याय शोधा.</p></div>
      <div className="grid two">
        <form className="card form" onSubmit={submit}>
          <label>पीक<select name="crop_name" value={form.crop_name} onChange={update} required><option value="">पीक निवडा</option>{crops.map((crop) => <option key={crop.id} value={crop.name_en}>{crop.name_mr || crop.name_en} – {crop.name_en}</option>)}</select></label>
          <label>प्रमाण (kg)<input name="quantity" type="number" min="1" value={form.quantity} onChange={update} /></label>
          <label>सध्याचा भाव (₹/kg)<input name="current_price" type="number" min="0.1" step="0.1" value={form.current_price} onChange={update} /></label>
          <label>उत्पादन खर्च (₹/kg)<input name="production_cost" type="number" min="0" step="0.1" value={form.production_cost} onChange={update} /></label>
          <label>वाहतूक खर्च (₹/kg)<input name="transport_cost" type="number" min="0" step="0.1" value={form.transport_cost} onChange={update} /></label>
          <label>साठवण खर्च (₹/kg/month)<input name="storage_cost" type="number" min="0" step="0.1" value={form.storage_cost} onChange={update} /></label>
          <button className="button primary" type="submit">AI विश्लेषण करा</button>
          {error && <p className="error">{error}</p>}
        </form>
        <div className="card result">{result ? <><p className="eyebrow">Numerical AI Recommendation</p><h2>{result.best_strategy}</h2><p>{result.reason}</p><div className="metrics"><strong>₹{Number(result.expected_profit).toLocaleString('en-IN')}<small> अपेक्षित नफा</small></strong><strong>{result.risk}<small> जोखीम</small></strong></div><button className="button primary ai-button" type="button" onClick={askAi} disabled={aiLoading}>{aiLoading ? 'AI सल्ला तयार करत आहे...' : 'AI कडून शेतकरी सल्ला घ्या'}</button>{aiAdvice && <div className="ai-advice"><p className="eyebrow">AI Farmer Guidance</p><div className="advice-text">{aiAdvice}</div></div>}</> : <p>डावीकडील माहिती भरून AI विश्लेषण सुरू करा.</p>}</div>
      </div>
      <div className="card ai-help-card"><div><p className="eyebrow">AI Farm Help</p><h2>शेतीबद्दल कोणताही प्रश्न विचारा</h2><p>पिकाची निगा, सिंचन, कापणीची तयारी किंवा खर्च कमी करण्याबद्दल मार्गदर्शन मिळवा.</p></div><form onSubmit={askFarmQuestion} className="ai-question-form"><textarea value={question} onChange={(event) => setQuestion(event.target.value)} maxLength="1200" placeholder="उदा. टोमॅटोची काढणीपूर्वी कोणती काळजी घ्यावी?" required /><div className="question-footer"><small>{question.length}/1200</small><button className="button primary" type="submit" disabled={questionLoading}>{questionLoading ? 'AI उत्तर तयार करत आहे...' : 'AI ला विचारा'}</button></div></form>{questionAnswer && <div className="ai-advice"><p className="eyebrow">AI Farmer Help</p><div className="advice-text">{questionAnswer}</div></div>}</div>
    </section>
  );
}
