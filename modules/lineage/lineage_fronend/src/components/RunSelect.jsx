export function RunSelect({ runs, selectedRun, onChange }) {
  return (
    <select
      value={selectedRun || ""}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">Selecione uma run</option>
      {runs.map((run) => (
        <option key={run} value={run}>
          {run}
        </option>
      ))}
    </select>
  );
}
