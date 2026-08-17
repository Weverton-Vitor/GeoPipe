import PipelineStep from "./PipelineStep";

import styles from "./RunPipeline.module.css";

export default function RunPipeline({
  stages,
}) {
  return (
    <section className={styles.container}>
      <div className={styles.label}>
        PIPELINE
      </div>

      <div className={styles.pipeline}>
        {stages.map((stage, index) => (
          <PipelineStep
            key={stage.id}
            stage={stage}
            isLast={
              index === stages.length - 1
            }
          />
        ))}
      </div>
    </section>
  );
}