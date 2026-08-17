import styles from "./PipelineStep.module.css";

export default function PipelineStep({
  stage,
  isLast,
}) {
  return (
    <div className={styles.wrapper}>
      <div
        className={`${styles.step} ${
          styles[stage.status]
        }`}
      >
        <div className={styles.icon}>
          {getIcon(stage.status)}
        </div>

        <div className={styles.text}>
          <strong>{stage.name}</strong>

          <span>
            {stage.status === "skipped"
              ? "Opcional"
              : stage.method}
          </span>
        </div>
      </div>

      {!isLast && (
        <div
          className={`${styles.connector} ${
            stage.status === "completed"
              ? styles.connectorDone
              : ""
          }`}
        />
      )}
    </div>
  );
}

function getIcon(status) {
  switch (status) {
    case "completed":
      return "✓";

    case "running":
      return "▶";

    case "failed":
      return "!";

    case "skipped":
      return "—";

    default:
      return "○";
  }
}