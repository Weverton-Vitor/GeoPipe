import styles from "./RunCard.module.css";
import { useNavigate } from "react-router-dom";

function getStatusLabel(status) {
  const labels = {
    completed: "Concluída",
    running: "Em execução",
    failed: "Falhou",
    pending: "Aguardando",
  };

  return labels[status] || status;
}

export default function RunCard({ run }) {
  const navigate = useNavigate();

  function handleOpenRun() {
    navigate(
      `/projects/${run.projectId}/runs/${run.id}`
    );
  }

  return (
    <article className={styles.card}>
      <div className={styles.main}>
        <div className={styles.runIcon}>
          #{String(run.id).slice(-2)}
        </div>

        <div className={styles.info}>
          <div className={styles.titleRow}>
            <h3>{run.name}</h3>

            <span
              className={`${styles.status} ${
                styles[run.status]
              }`}
            >
              <span className={styles.statusDot} />

              {getStatusLabel(run.status)}
            </span>
          </div>

          <p>
            {new Date(run.createdAt).toLocaleString(
              "pt-BR"
            )}
          </p>
        </div>
      </div>

      <div className={styles.pipeline}>
        <PipelineStep
          label="Download"
          enabled
        />

        <PipelineStep
          label="Nuvens"
          enabled={run.cloudDetection}
          optional
        />

        <PipelineStep
          label="Reconstrução"
          enabled={run.reconstruction}
          optional
        />

        <PipelineStep
          label="Água"
          enabled
        />

        <PipelineStep
          label="Volume"
          enabled
        />

        <PipelineStep
          label="Métricas"
          enabled={run.metrics}
        />
      </div>

      <div className={styles.details}>
        <div>
          <span>Satélite</span>
          <strong>{run.satellite}</strong>
        </div>

        <div>
          <span>Segmentação</span>
          <strong>{run.waterSegmentation}</strong>
        </div>

        <button
          type="button"
          className={styles.openButton}
          onClick={handleOpenRun}
        >
          Abrir run →
        </button>
      </div>
    </article>
  );
}

function PipelineStep({
  label,
  enabled,
  optional = false,
}) {
  return (
    <div
      className={`${styles.step} ${
        enabled ? styles.enabled : styles.disabled
      }`}
    >
      <div className={styles.stepIndicator}>
        {enabled ? "✓" : "—"}
      </div>

      <span>{label}</span>

      {optional && (
        <small>opcional</small>
      )}
    </div>
  );
}