import styles from "./RunSelect.module.css";

export function Select({ options, selectedOption, onChange }) {
  return (
    <select
      className={styles.darkSelect}
      value={selectedOption || ""}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">Selecione um experimento</option>
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}
