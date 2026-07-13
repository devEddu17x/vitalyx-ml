import { CheckCircle2, Send, X } from "lucide-react";

import type { Evidence, EvidenceLabelMap, FriendlyAnswer } from "../lib/types";

interface SelectedAnswersProps { evidences: Evidence[]; answers: Record<string, FriendlyAnswer | undefined>; valueLabels: EvidenceLabelMap; onRemove: (evidenceId: string) => void; }

function answerValue(evidence: Evidence, answer: FriendlyAnswer, valueLabels: EvidenceLabelMap) { const label = (value: string) => valueLabels[evidence.id]?.[value] ?? value; if ("present" in answer) return "Present"; if ("value" in answer) return label(answer.value); return answer.values.map(label).join(", "); }

export function SelectedAnswers({ evidences, answers, valueLabels, onRemove }: SelectedAnswersProps) {
  const payload = evidences.flatMap((evidence) => answers[evidence.id] ? [{ evidence, answer: answers[evidence.id] as FriendlyAnswer }] : []);
  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><div className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-emerald-50 text-emerald-700"><Send className="size-4" /></span><div><h2 className="font-semibold text-slate-950">Request preview</h2><p className="text-sm text-slate-500">Only observed answers are sent to the model.</p></div></div><span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700">{payload.length} answers</span></div>{payload.length === 0 ? <p className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-500">Choose “Present”, a single option, or one or more multiple-choice values to build a request.</p> : <div className="mt-4 space-y-2">{payload.map(({ evidence, answer }) => <div key={evidence.id} className="flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-2.5"><CheckCircle2 className="size-4 shrink-0 text-emerald-600" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-slate-800">{evidence.question}</p><p className="truncate text-xs text-slate-500">{answerValue(evidence, answer, valueLabels)}</p></div><button type="button" onClick={() => onRemove(evidence.id)} className="rounded-md p-1 text-slate-400 hover:bg-white hover:text-red-600" aria-label={`Remove ${evidence.question}`}><X className="size-4" /></button></div>)}</div>}</section>;
}
