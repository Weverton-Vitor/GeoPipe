export function adaptTimeseriesResponse(raw) {
    if (!raw || !raw.volume || !raw.year) return [];

    let size = raw.year.length;
    const result_volumes = [];

    for (let i = 0; i < size; i++) {
        result_volumes.push({
            day: raw.day[i],
            year: raw.year[i],
            month: raw.month[i],
            volume_m2: raw.volume_m2[i],
            cloud: raw.CLOUDY_PIXEL_PERCENTAGE[i],
            label: `${raw.month[i]}/${raw.year[i]}`,
        });
    }


    return result_volumes
}
