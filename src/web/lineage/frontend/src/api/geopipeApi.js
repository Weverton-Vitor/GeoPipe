const BASE_URL = "http://localhost:8080";

export async function getRuns() {
    const res = await fetch(`${BASE_URL}/runs/`);
    return res.json();
}

export async function getVolumeTimeSeries(segmentationMethod, runName) {
    const res = await fetch(
        `${BASE_URL}/timeseries/volume?segmentation_method=${segmentationMethod}&run_name=${runName}`
    );
    return res.json();
}

export async function getImagesForMonth(runId, year, month) {
    console.log("Fetching images for:", runId, year, month);

    const res = await fetch(
        `${BASE_URL}/images/get_for_month?year=${year}&month=${month}&run_name=${runId}`
    );

    return res.json();
}

export async function getImagesForDay(runId, year, month, day) {
    console.log("Fetching images for:", runId, year, month, day);

    const res = await fetch(
        `${BASE_URL}/images/get_for_day?year=${year}&month=${month}&day=${day}&run_name=${runId}`
    );

    return res.json();
}

export async function getImagesArtifacts(runId, year, month, day) {
    console.log("Fetching images for:", runId, year, month, day);

    const res = await fetch(
        `${BASE_URL}/artifacts/get_artifacts?year=${year}&month=${month}&day=${day}&run_name=${runId}`
    );

    return res.json();
}

export async function getWatermask(
    runId,
    year,
    month,
    day,
    threshold
) {
    console.log(
        "Fetching water mask for:",
        runId,
        year,
        month,
        day,
        threshold
    );

    const res = await fetch(
        `${BASE_URL}/artifacts/get_water_mask?year=${year}&month=${month}&day=${day}&run_name=${runId}&threshold=${threshold}`
    );

    return res.json();
}


// ==========================================
// PROJETOS
// ==========================================

export async function createProject(form) {
    const formData = new FormData();

    formData.append("name", form.name);
    formData.append("location", form.location);
    formData.append("description", form.description);

    if (form.shapefile) {
        formData.append("shapefile", form.shapefile);
    }

    if (form.elevationFile) {
        formData.append(
            "elevationFile",
            form.elevationFile
        );
    }

    if (form.volumeFile) {
        formData.append(
            "volumeFile",
            form.volumeFile
        );
    }

    const res = await fetch(`${BASE_URL}/projects/`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        throw new Error(
            `Erro ao criar projeto: ${res.status}`
        );
    }

    return res.json();
}