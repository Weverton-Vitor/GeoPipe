import styles from "./RealVolumesTable.module.css";

export default function RealVolumesTable({ data }) {
  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Data</th>
            <th>Cota (m)</th>
            <th>Volume (m³)</th>
          </tr>
        </thead>

        <tbody>
          {data.map((item, index) => (
            <tr key={`${item.date}-${index}`}>
              <td>
                {new Date(
                  `${item.date}T00:00:00`
                ).toLocaleDateString("pt-BR")}
              </td>

              <td>
                {item.elevation.toFixed(2)}
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