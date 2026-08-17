import styles from "./RunHeader.module.css";

export default function RunHeader({ run }) {
  const status = getStatus(run.status);

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <button
          type="button"
          className={styles.back}
        >
          ←
          <span>
            {run.project.name}
          </span>
        </button>

        <div className={styles.content}>
          <div>
            <span className={styles.eyebrow}>
              RUN #{String(run.id).padStart(3, "0")}
            </span>

            <h1>{run.name}</h1>

            <p>
              {run.project.location} · {run.year}
            </p>
          </div>

          <div className={styles.info}>
            <div
              className={`${styles.status} ${styles[status.className]}`}
            >
              <span />

              {status.label}
            </div>

            <div className={styles.meta}>
              <span>
                Iniciada
              </span>

              <strong>
                {run.startedAt}
              </strong>
            </div>

            <div className={styles.meta}>
              <span>
                Tempo
              </span>

              <strong>
                {run.elapsedTime}
              </strong>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function getStatus(status) {
  const statuses = {
    running: {
      label: "Executando",
      className: "running",
    },

    completed: {
      label: "Concluída",
      className: "completed",
    },

    failed: {
      label: "Falhou",
      className: "failed",
    },

    pending: {
      label: "Pendente",
      className: "pending",
    },
  };

  return statuses[status] ?? statuses.pending;
}