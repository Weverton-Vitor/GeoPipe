import { useState } from "react";
import styles from "./ImageViewer.module.css";

const API_BASE = "http://localhost:8080";

export function ImageViewer({ imageUrl, artifacts, onClose }) {
  const [showCloudMask, setShowCloudMask] = useState(false);
  const [maskOpacity, setMaskOpacity] = useState(0.5);

  if (!artifacts) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.header}>
          <h4>Comparação</h4>
          <button onClick={onClose}>✕</button>
        </div>

        <div className={styles.imageContainer}>
          
          {/* ================= ORIGINAL ================= */}
          <div className={styles.imageBlock}>
            <h5>Original</h5>

            <button
              className={styles.toggleButton}
              onClick={() => setShowCloudMask(!showCloudMask)}
            >
              {showCloudMask ? "Ocultar Máscara" : "Mostrar Máscara"}
            </button>

            {showCloudMask && (
              <div className={styles.sliderContainer}>
                <label>Opacidade:</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={maskOpacity}
                  onChange={(e) =>
                    setMaskOpacity(parseFloat(e.target.value))
                  }
                />
              </div>
            )}

            <div className={styles.imageWrapper}>
              {imageUrl && (
                <img
                  src={API_BASE + imageUrl}
                  alt="Original"
                  className={styles.baseImage}
                />
              )}

              {showCloudMask && artifacts.cloud_mask && (
                <img
                  src={API_BASE + artifacts.cloud_mask.path}
                  alt="Cloud Mask"
                  className={styles.overlayImage}
                  style={{ opacity: maskOpacity }}
                />
              )}
            </div>
          </div>

          {/* ================= CLOUD FREE ================= */}
          <div className={styles.imageBlock}>
            <h5>Cloud Free</h5>

            {artifacts.clean && (
              <img
                src={API_BASE + artifacts.clean.path}
                alt="Cloud Free"
                className={styles.baseImage}
              />
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
