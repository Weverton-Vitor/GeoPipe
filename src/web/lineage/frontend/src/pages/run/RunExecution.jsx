import styles from "./RunExecution.module.css";

export default function RunExecution({ run }) {
  const stage = run.stages.find(
    (item) => item.id === run.currentStage
  );

  if (!stage) {
    return null;
  }

  return (
    <section className={styles.container}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            EXECUÇÃO ATUAL
          </span>

          <h2>{stage.name}</h2>

          <p>
            {stage.method}
          </p>
        </div>

        <strong>
          {run.progress.percentage}%
        </strong>
      </div>

      <div className={styles.progress}>
        <div
          style={{
            width: `${run.progress.percentage}%`,
          }}
        />
      </div>

      <div className={styles.footer}>
        <span>
          Processando imagem{" "}
          <strong>
            {run.progress.current}
          </strong>{" "}
          de{" "}
          <strong>
            {run.progress.total}
          </strong>
        </span>

        <span>
          {run.progress.percentage}% concluído
        </span>
      </div>
    </section>
  );
}