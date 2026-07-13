import { Info } from "lucide-react";

export function AcademicDisclaimer() {
  return (
    <div className="flex gap-3 rounded-2xl border border-cyan-100 bg-cyan-50/80 px-4 py-3 text-sm text-slate-700">
      <Info className="mt-0.5 size-4 shrink-0 text-cyan-700" />
      <p><strong className="font-semibold text-slate-900">Academic orientation tool.</strong> Vitalyx was trained with synthetic patient data. Results are not a medical diagnosis and must not replace professional care.</p>
    </div>
  );
}
