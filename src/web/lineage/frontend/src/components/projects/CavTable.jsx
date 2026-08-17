import styles from "./CavTable.module.css";

export default function CavTable({ data }) {
  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Cota (m)</th>
            <th>Área (m²)</th>
            <th>Volume (m³)</th>
          </tr>
        </thead>

        <tbody>
          {data.map((item, index) => (
            <tr key={`${item.elevation}-${index}`}>
              <td>
                {item.elevation.toFixed(2)}
              </td>

              <td>
                {item.area.toLocaleString("pt-BR")}
              </td>

              <td>
                {item.volume.toLocaleString("pt-BR")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}