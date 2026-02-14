import { useEffect, useState } from "react";
import {
  getRuns,
  getVolumeTimeSeries,
  getImagesForDay,
} from "../api/geopipeApi";

import { RunSelect } from "../components/RunSelect";
import { VolumeChart } from "../components/VolumeChart";
import { ImageGallery } from "../components/ImageGallery";
import { ImageViewer } from "../components/ImageViewer";

import { adaptTimeseriesResponse } from "../adapters/timeseriesAdapter";
export function LineagePage() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [timeseries, setTimeseries] = useState([]);
  const [images, setImages] = useState([]);          // ⬅ array
  const [selectedImage, setSelectedImage] = useState({"url": ""}); // ⬅ objeto

  useEffect(() => {
    getRuns().then(setRuns);
  }, []);

  useEffect(() => {
    if (!selectedRun) return;

    async function loadTimeseries() {
      const raw = await getVolumeTimeSeries("vggunet", selectedRun);
      const adapted = adaptTimeseriesResponse(raw);
      setTimeseries(adapted);
    }

    loadTimeseries();
  }, [selectedRun]);

  const selectImage = (image) => {
    console.log("Imagem selecionada:", image);
    setSelectedImage(image);
  }

  async function handleSelectMonth(year, month, day) {
    if (!selectedRun) return;

    try {
      setSelectedImage({"url": ""});
      setImages([]);

      const paddedMonth = String(month).padStart(2, "0");

      const response = await getImagesForDay(
        selectedRun,
        year,
        paddedMonth,
        day
      );

      setImages(response.images || []);
    } catch (err) {
      console.error("Erro ao buscar imagens:", err);
    }
  }

  return (
    <div style={{ width: "90vw" }}>
      <RunSelect
        runs={runs}
        selectedRun={selectedRun}
        onChange={setSelectedRun}
      />

      {timeseries.length > 0 && (
        <VolumeChart
          data={timeseries}
          onSelect={handleSelectMonth}
        />
      )}

      <ImageGallery
        images={images}
        onSelect={selectImage}
      />

      <ImageViewer imageUrl={selectedImage.url} onClose={() => {}}/>

    </div>
  );
}
    