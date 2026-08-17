import { useState } from "react";

import { runMock } from "../../mocks/runMock";

import RunHeader from "./RunHeader";
import RunPipeline from "./RunPipeline";
import RunExecution from "./RunExecution";
import StageResult from "./StageResult";

import styles from "./RunPage.module.css";

export default function RunPage() {
  const [run] = useState(runMock);

  const [selectedArtifact, setSelectedArtifact] =
    useState(null);

  return (
    <main className={styles.page}>
      <RunHeader run={run} />

      <section className={styles.container}>
        <RunPipeline stages={run.stages} />

        {run.status === "running" && (
          <RunExecution
            run={run}
          />
        )}

        <section className={styles.results}>
          <div className={styles.resultsHeader}>
            <div>
              <span className={styles.eyebrow}>
                RESULTADOS
              </span>

              <h2>Saídas do processamento</h2>

              <p>
                Artefatos produzidos por cada etapa
                desta run.
              </p>
            </div>
          </div>

          <div className={styles.stages}>
            {run.stages.map((stage) => (
              <StageResult
                key={stage.id}
                stage={stage}
                onArtifactClick={setSelectedArtifact}
              />
            ))}
          </div>
        </section>
      </section>

      {selectedArtifact && (
        <ArtifactModal
          artifact={selectedArtifact}
          onClose={() =>
            setSelectedArtifact(null)
          }
        />
      )}
    </main>
  );
}

function ArtifactModal({
  artifact,
  onClose,
}) {
  return (
    <div
      className={styles.modalOverlay}
      onMouseDown={onClose}
    >
      <div
        className={styles.modal}
        onMouseDown={(event) =>
          event.stopPropagation()
        }
      >
        <header className={styles.modalHeader}>
          <div>
            <span>ARTEFATO</span>

            <h2>{artifact.name}</h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className={styles.close}
          >
            ×
          </button>
        </header>

        <div className={styles.modalBody}>
          {artifact.type === "image" ||
          artifact.type === "mask" ? (
            <img
              src={artifact.url}
              alt={artifact.name}
            />
          ) : (
            <div>
              Arquivo não possui preview.
            </div>
          )}
        </div>

        <footer className={styles.modalFooter}>
          <span>{artifact.type}</span>

          <button
            type="button"
            className={styles.download}
          >
            Download
          </button>
        </footer>
      </div>
    </div>
  );
}