import styles from "./ImageGallery.module.css";

export function ImageGallery({ images, onSelect }) {
  if (!images || images.length === 0) return null;

  return (
    <div className={styles.gallery}>
      {images.map((img) => (
        <div
          key={img.url}
          className={styles.thumbWrapper}
          onClick={() => {
    console.log("CLIQUEI", img);
    onSelect(img);
  }}
        >
          <img
            src={"http://localhost:8080" + img.url}
            alt={img.name}
            className={styles.thumbnail}
            loading="lazy"
          />
          <div className={styles.caption}>
            {img.name.replace(".tif", "")}
          </div>
        </div>
      ))}
    </div>
  );
}
