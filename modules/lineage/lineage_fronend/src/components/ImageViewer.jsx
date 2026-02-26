import { useState } from "react";
import styles from "./ImageViewer.module.css";
import { getWatermask } from "../api/geopipeApi";

const API_BASE = "http://localhost:8080";

export function ImageViewer({ selectedRun, selected_date, imageUrl, artifacts, onClose }) {
  const [showCloudMask, setShowCloudMask] = useState(false);
  const [maskOpacity, setMaskOpacity] = useState(0.5);

  const [showProbability, setShowProbability] = useState(true);
  const [probOpacity, setProbOpacity] = useState(0.7);

  const [showBinaryMask, setShowBinaryMask] = useState(false);
  const [binaryOpacity, setBinaryOpacity] = useState(0.8);

  const [threshold, setThreshold] = useState(0.5);
  const [pendingThreshold, setPendingThreshold] = useState(0.5);
  const [binaryMaskUrl, setBinaryMaskUrl] = useState(null);
  const [showRightShapefile, setShowRightShapefile] = useState(false);
  const [showLeftShapefile, setShowLeftShapefile] = useState(false);


  async function handleApplyThreshold() {

    const value = parseFloat(pendingThreshold);

    if (isNaN(value) || value < 0 || value > 2) return;

    const waterMask = await getWatermask(
      selectedRun,
      selected_date.year,
      selected_date.month,
      selected_date.day,
      threshold
    );
    setBinaryMaskUrl(API_BASE + waterMask.path);
    setThreshold(value);
  }

  function handleThresholdKeyDown(e) {
    if (e.key === "Enter") handleApplyThreshold();
  }

  if (!artifacts) return null;

  const dateStr = `${String(selected_date.day).padStart(2, "0")}/${String(selected_date.month).padStart(2, "0")}/${selected_date.year}`;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerBadge}>
            <h4>Análise de Imagens</h4>
          </div>
          <button className={styles.closeButton} onClick={onClose}>✕</button>
        </div>


        <div className={styles.modalContent}>
          <div className={styles.imageContainerContent}>

            {/* PAINEL ORIGINAL */}
            <p className={styles.panelTitle}>Imagem Original</p>
            <p className={styles.panelDate}>{dateStr}</p>
            <div className={styles.imageBlock}>


              <div className={styles.imageWrapper}>
                {imageUrl && (
                  <img src={API_BASE + imageUrl} alt="Original" className={styles.baseImage} />
                )}
                {showCloudMask && artifacts.cloud_mask && (
                  <img
                    src={API_BASE + artifacts.cloud_mask.path}
                    alt="Cloud Mask"
                    className={styles.overlayImage}
                    style={{ opacity: maskOpacity }}
                  />
                )}
                {showLeftShapefile && artifacts.shapefile && (
                  <img
                    src={API_BASE + artifacts.shapefile.path}
                    alt="Shapefile"
                    className={styles.overlayImage}

                    crossOrigin="anonymous"
                  />
                )}
              </div>
              

              <div className={styles.controls}>
                <div className={styles.controlCard}>
                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={showLeftShapefile}
                      onChange={() => setShowLeftShapefile(!showLeftShapefile)}
                    />
                    <span className={styles.checkLabel}>Shapefile</span>
                  </label> 

                  <button
                    className={`${styles.toggleButton} ${showCloudMask ? styles.active : ""}`}
                    onClick={() => setShowCloudMask(!showCloudMask)}
                  >
                    {showCloudMask ? "Ocultar Máscara de Nuvem" : "Mostrar Máscara de Nuvem"}
                  </button>

                  {showCloudMask && (
                    <div className={styles.sliderContainer}>
                      <div className={styles.sliderLabel}>
                        <span>Opacidade</span>
                        <span>{maskOpacity.toFixed(1)}</span>
                      </div>
                      <input
                        type="range"
                        min="0" max="1" step="0.1"
                        value={maskOpacity}
                        onChange={(e) => setMaskOpacity(parseFloat(e.target.value))}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>


          {/* PAINEL CLOUD FREE */}
          <div className={styles.imageContainerContent}>
              <p className={styles.panelTitle}>Cloud Free</p>
              <p className={styles.panelDate}>Water Analysis</p>
            <div className={styles.imageBlock}>

              {/* Camadas */}
              <div className={styles.imageWrapper}>
                {artifacts.clean && (
                  <img
                    src={API_BASE + artifacts.clean.path}
                    alt="Cloud Free"
                    className={styles.baseImage}
                    crossOrigin="anonymous"
                  />
                )}
                {showProbability && artifacts.water_mask && (
                  <img
                    src={API_BASE + artifacts.water_mask.path}
                    alt="Probability"
                    className={styles.overlayImage}
                    style={{ opacity: probOpacity }}
                    crossOrigin="anonymous"
                  />
                )}
                {showBinaryMask && binaryMaskUrl && (
                  <img
                    src={binaryMaskUrl}
                    alt="Binary Mask"
                    className={styles.overlayImage}
                    style={{ opacity: binaryOpacity }}
                    crossOrigin="anonymous"
                  />
                )}
                {showRightShapefile && artifacts.shapefile && (
                  <img
                    src={API_BASE + artifacts.shapefile.path}
                    alt="Shapefile"
                    className={styles.overlayImage}

                    crossOrigin="anonymous"
                  />
                )}


              </div>
              <div className={styles.controls}>

                <div className={styles.controlCard}>
                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={showRightShapefile}
                      onChange={() => setShowRightShapefile(!showRightShapefile)}
                    />
                    <span className={styles.checkLabel}>Shapefile</span>
                  </label>

                {/* Probabilidade */}

                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={showProbability}
                      onChange={() => setShowProbability(!showProbability)}
                    />
                    <span className={styles.checkLabel}>Probabilidade de Água</span>
                  </label>

                  {showProbability && (
                    <div className={styles.sliderContainer}>
                      <div className={styles.sliderLabel}>
                        <span>Opacidade</span>
                        <span>{probOpacity.toFixed(2)}</span>
                      </div>
                      <input
                        type="range"
                        min="0" max="1" step="0.05"
                        value={probOpacity}
                        onChange={(e) => setProbOpacity(parseFloat(e.target.value))}
                      />
                    </div>
                  )}
                </div>

                {/* Máscara Binária */}
                <div className={styles.controlCard}>
                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={showBinaryMask}
                      onChange={() => setShowBinaryMask(!showBinaryMask)}
                    />
                    <span className={styles.checkLabel}>Máscara Binária</span>
                  </label>

                  {showBinaryMask && (
                    <>
                      <hr className={styles.divider} />
                      <div className={styles.sliderLabel} style={{ paddingLeft: "26px" }}>
                        <span>Threshold</span>
                      </div>
                      <div className={styles.thresholdRow}>
                        <input
                          type="number"
                          className={styles.thresholdInput}
                          min="0" max="1" step="0.01"
                          value={pendingThreshold}
                          onChange={(e) => setPendingThreshold(e.target.value)}
                          onKeyDown={handleThresholdKeyDown}
                        />
                        <button className={styles.applyButton} onClick={handleApplyThreshold}>
                          Aplicar
                        </button>
                      </div>
                      <span className={styles.thresholdApplied}>
                        Aplicado: {threshold.toFixed(2)}
                      </span>
                      <hr className={styles.divider} />
                      <div className={styles.sliderContainer}>
                        <div className={styles.sliderLabel}>
                          <span>Opacidade</span>
                          <span>{binaryOpacity.toFixed(2)}</span>
                        </div>
                        <input
                          type="range"
                          min="0" max="1" step="0.05"
                          value={binaryOpacity}
                          onChange={(e) => setBinaryOpacity(parseFloat(e.target.value))}
                        />
                      </div>
                    </>
                  )}
                </div>

                

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}