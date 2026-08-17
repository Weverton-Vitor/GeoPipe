import styles from "./ArtifactPreview.module.css";

export default function ArtifactPreview({
  artifact,
  onClick,
}) {
  const isImage =
    artifact.type === "image" ||
    artifact.type === "mask";

  return (
    <button
      type="button"
      className={styles.card}
      onClick={onClick}
    >
      <div className={styles.preview}>
        {isImage ? (
          <img
            src={artifact.url}
            alt={artifact.name}
          />
        ) : (
          <div className={styles.file}>
            FILE
          </div>
        )}
      </div>

      <div className={styles.info}>
        <strong>{artifact.name}</strong>

        <span>
          {artifact.role === "input"
            ? "Entrada"
            : "Saída"}
        </span>
      </div>
    </button>
  );
}