import ArtifactPreview from "./ArtifactPreview";

import styles from "./StageResult.module.css";

export default function StageResult({
  stage,
  onArtifactClick,
}) {
  const hasArtifacts =
    stage.artifacts &&
    stage.artifacts.length > 0;

  return (
    <section className={styles.container}>
      <header className={styles.header}>
        <div className={styles.title}>
          <span className={styles.number}>
            {stage.number}
          </span>

          <div>
            <h3>{stage.name}</h3>

            <span>{stage.method}</span>
          </div>
        </div>

        <Status status={stage.status} />
      </header>

      {stage.status === "running" && (
        <div className={styles.running}>
          <span className={styles.spinner} />

          Processando esta etapa...
        </div>
      )}

      {stage.status === "pending" && (
        <div className={styles.empty}>
          Esta etapa ainda não foi executada.
        </div>
      )}

      {stage.status === "skipped" && (
        <div className={styles.empty}>
          Esta etapa foi desabilitada nesta run.
        </div>
      )}

      {stage.status === "failed" && (
        <div className={styles.error}>
          Esta etapa apresentou um erro durante a
          execução.
        </div>
      )}

      {hasArtifacts && (
        <div className={styles.artifacts}>
          {stage.artifacts.map((artifact) => (
            <ArtifactPreview
              key={artifact.id}
              artifact={artifact}
              onClick={() =>
                onArtifactClick(artifact)
              }
            />
          ))}
        </div>
      )}

      {stage.result && (
        <div className={styles.result}>
          Resultado: {stage.result}
        </div>
      )}

      {stage.metrics?.length > 0 && (
        <div className={styles.metrics}>
          {stage.metrics.map((metric) => (
            <div key={metric.name}>
              <span>{metric.name}</span>

              <strong>
                {metric.value}
              </strong>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function Status({ status }) {
  const config = {
    completed: {
      label: "Concluída",
      className: "completed",
    },

    running: {
      label: "Executando",
      className: "running",
    },

    pending: {
      label: "Pendente",
      className: "pending",
    },

    skipped: {
      label: "Ignorada",
      className: "skipped",
    },

    failed: {
      label: "Falhou",
      className: "failed",
    },
  };

  const current =
    config[status] ?? config.pending;

  return (
    <span
      className={`${styles.status} ${styles[current.className]}`}
    >
      <span />

      {current.label}
    </span>
  );
}