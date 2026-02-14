import styles from "./ImageViewer.module.css";

export function ImageViewer({ image, onClose }) {
  if (!image) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
        <p>aaaaaaaaaaaaa</p>
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()} // evita fechar ao clicar na imagem
      >
        <div className={styles.header}>
          <h4>{image.name}</h4>
          <button onClick={onClose}>✕</button>
        </div>

        <img
          src={"http://localhost:8080" + image.url}
          alt={image.name}
          className={styles.image}
        />
      </div>
    </div>
  );
}
