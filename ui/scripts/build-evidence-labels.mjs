import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const projectDirectory = resolve(scriptDirectory, "..");
const sourcePath = process.argv[2] ? resolve(process.argv[2]) : resolve(projectDirectory, "release_evidences.json");
const outputPath = resolve(projectDirectory, "public", "evidence-labels.json");

const source = JSON.parse(await readFile(sourcePath, "utf8"));
const valueLabels = {};

for (const [evidenceId, evidence] of Object.entries(source)) {
  const meanings = evidence.value_meaning;
  if (!meanings || typeof meanings !== "object") continue;
  const labels = {};
  for (const [value, meaning] of Object.entries(meanings)) {
    const english = typeof meaning === "object" && meaning ? meaning.en : undefined;
    labels[String(value)] = typeof english === "string" && english.trim() ? english : String(value);
  }
  if (Object.keys(labels).length) valueLabels[evidenceId] = labels;
}

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify({ value_labels: valueLabels }, null, 2)}\n`, "utf8");
console.log(`Generated ${outputPath} with ${Object.keys(valueLabels).length} evidence mappings.`);
