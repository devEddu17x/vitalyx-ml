import { Activity, ArrowRight, LoaderCircle, Stethoscope } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { AcademicDisclaimer } from "./components/AcademicDisclaimer";
import { EvidenceCatalog, SelectedEvidenceForm } from "./components/EvidencePicker";
import { PatientForm } from "./components/PatientForm";
import { PredictionResults } from "./components/PredictionResults";
import { SelectedAnswers } from "./components/SelectedAnswers";
import { createPrediction, getEvidenceLabels, getEvidences } from "./lib/api";
import type { Evidence, EvidenceLabelMap, FriendlyAnswer, PredictionResponse } from "./lib/types";

function App() {
  const [age, setAge] = useState("");
  const [sex, setSex] = useState<"F" | "M">("F");
  const [evidences, setEvidences] = useState<Evidence[]>([]);
  const [valueLabels, setValueLabels] = useState<EvidenceLabelMap>({});
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [answers, setAnswers] = useState<Record<string, FriendlyAnswer | undefined>>({});
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { Promise.all([getEvidences(), getEvidenceLabels().catch(() => ({}))]).then(([catalog, labels]) => { setEvidences(catalog.items); setValueLabels(labels); }).catch((error: unknown) => setCatalogError(error instanceof Error ? error.message : "Unable to load the evidence catalog.")); }, []);

  const predictionAnswers = useMemo(() => Object.values(answers).filter((answer): answer is FriendlyAnswer => Boolean(answer)), [answers]);
  const selectedEvidences = useMemo(() => evidences.filter((evidence) => selectedIds.includes(evidence.id)), [evidences, selectedIds]);
  const ageNumber = Number(age);
  const hasValidAge = age.trim() !== "" && Number.isFinite(ageNumber) && ageNumber >= 0 && ageNumber <= 109;
  const canSubmit = hasValidAge && predictionAnswers.length > 0 && !loading;

  function addEvidence(evidence: Evidence) { setSelectedIds((current) => current.includes(evidence.id) ? current : [...current, evidence.id]); }
  function removeEvidence(evidenceId: string) { setSelectedIds((current) => current.filter((id) => id !== evidenceId)); setAnswers((current) => { const next = { ...current }; delete next[evidenceId]; return next; }); }
  function updateAnswer(evidenceId: string, answer: FriendlyAnswer | undefined) { setAnswers((current) => { const next = { ...current }; if (answer) next[evidenceId] = answer; else delete next[evidenceId]; return next; }); }

  async function handlePrediction() { if (!canSubmit) return; setLoading(true); setPredictionError(null); setResult(null); try { setResult(await createPrediction({ age: ageNumber, sex, answers: predictionAnswers, top_k: 5 })); } catch (error: unknown) { setPredictionError(error instanceof Error ? error.message : "Unable to generate orientation results."); } finally { setLoading(false); } }

  return <main className="min-h-screen bg-[#f4f7fb] text-slate-950"><div className="mx-auto max-w-[1500px] px-4 py-5 sm:px-6 lg:px-8 lg:py-8"><header className="relative overflow-hidden rounded-3xl bg-slate-950 px-6 py-7 text-white shadow-xl shadow-slate-900/10 sm:px-8"><div className="absolute -right-20 -top-24 size-72 rounded-full bg-cyan-500/20 blur-3xl" /><div className="absolute bottom-0 left-1/3 size-44 rounded-full bg-blue-600/20 blur-3xl" /><div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-4"><span className="grid size-12 place-items-center rounded-2xl bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20"><Stethoscope className="size-6" /></span><div><p className="text-xl font-bold tracking-tight">Vitalyx</p><p className="mt-0.5 text-sm text-slate-300">AI-assisted pathology orientation</p></div></div><div className="flex items-center gap-2 self-start rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-200 sm:self-auto"><Activity className="size-3.5 text-cyan-300" />Synthetic-data academic model</div></div></header><div className="mt-5"><AcademicDisclaimer /></div>{catalogError && <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><strong>Evidence catalog unavailable.</strong> {catalogError}</div>}<div className="mt-6"><PatientForm age={age} sex={sex} onAgeChange={(event) => setAge(event.target.value)} onSexChange={setSex} /></div><div className="mt-6 grid gap-6 xl:grid-cols-[330px_minmax(0,1fr)_370px] xl:items-start"><EvidenceCatalog evidences={evidences} selectedIds={selectedIds} onAdd={addEvidence} onRemove={removeEvidence} /><div className="space-y-5"><SelectedEvidenceForm evidences={selectedEvidences} answers={answers} valueLabels={valueLabels} onRemove={removeEvidence} onAnswerChange={updateAnswer} /><SelectedAnswers evidences={selectedEvidences} answers={answers} valueLabels={valueLabels} onRemove={removeEvidence} /><button type="button" onClick={handlePrediction} disabled={!canSubmit} className="flex h-13 w-full items-center justify-center gap-2 rounded-2xl bg-cyan-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-cyan-700/20 transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none">{loading ? <><LoaderCircle className="size-4 animate-spin" />Analyzing possible pathologies…</> : <>Analyze possible pathologies <ArrowRight className="size-4" /></>}</button>{!canSubmit && !loading && <p className="text-center text-xs text-slate-500">Enter an age from 0 to 109 and add at least one observed answer to continue.</p>}</div><PredictionResults result={result} loading={loading} error={predictionError} /></div></div></main>;
}

export default App;
