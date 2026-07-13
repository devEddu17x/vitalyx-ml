import type { ChangeEvent } from "react";
import { CalendarDays, UserRound } from "lucide-react";

interface PatientFormProps {
  age: string;
  sex: "F" | "M";
  onAgeChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSexChange: (sex: "F" | "M") => void;
}

export function PatientForm({ age, sex, onAgeChange, onSexChange }: PatientFormProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-cyan-50 text-cyan-700"><UserRound className="size-4" /></span><div><h2 className="font-semibold text-slate-950">Patient information</h2><p className="text-sm text-slate-500">Start with the required demographic fields.</p></div></div>
      <div className="grid gap-5 sm:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]">
        <label className="grid gap-2 text-sm font-medium text-slate-700" htmlFor="age"><span className="flex items-center gap-2"><CalendarDays className="size-4 text-cyan-700" />Age</span><input id="age" type="number" min="0" max="109" inputMode="numeric" placeholder="e.g. 32" value={age} onChange={onAgeChange} className="h-11 rounded-xl border border-slate-200 bg-slate-50 px-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-cyan-600 focus:bg-white focus:ring-4 focus:ring-cyan-100" /></label>
        <fieldset className="grid gap-2"><legend className="text-sm font-medium text-slate-700">Sex</legend><div className="grid grid-cols-2 rounded-xl border border-slate-200 bg-slate-50 p-1"><button type="button" onClick={() => onSexChange("F")} className={`rounded-lg px-4 py-2 text-sm font-medium transition ${sex === "F" ? "bg-white text-cyan-800 shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:text-slate-800"}`}>Female</button><button type="button" onClick={() => onSexChange("M")} className={`rounded-lg px-4 py-2 text-sm font-medium transition ${sex === "M" ? "bg-white text-cyan-800 shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:text-slate-800"}`}>Male</button></div></fieldset>
      </div>
    </section>
  );
}
