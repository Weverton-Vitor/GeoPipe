export const projectDetails = {
  1: {
    projectId: 1,

    name: "Sume - ROI Quadrada",

    location: "Sume, RN",

    description:
      "Projeto utilizando uma ROI quadrada para processamento do reservatório de Sume.",

    shapefileImage: "/images/sume-roi-quadrada.png",

    cav: [
      {
        elevation: 180,
        area: 0,
        volume: 0,
      },
      {
        elevation: 181,
        area: 12500,
        volume: 6200,
      },
      {
        elevation: 182,
        area: 28000,
        volume: 24500,
      },
      {
        elevation: 183,
        area: 46500,
        volume: 61000,
      },
      {
        elevation: 184,
        area: 69000,
        volume: 118500,
      },
      {
        elevation: 185,
        area: 92000,
        volume: 199000,
      },
    ],

    realVolumes: [
      {
        date: "2026-01-15",
        elevation: 181.8,
        volume: 22800,
        source: "Medição de campo",
      },
      {
        date: "2026-02-20",
        elevation: 182.4,
        volume: 37000,
        source: "Medição de campo",
      },
      {
        date: "2026-03-18",
        elevation: 183.1,
        volume: 64000,
        source: "Medição de campo",
      },
      {
        date: "2026-04-22",
        elevation: 183.7,
        volume: 92000,
        source: "Medição de campo",
      },
    ],

    runs: [
      {
        id: 101,
        name: "Run #001",
        status: "completed",
        createdAt: "2026-08-15T14:32:00",
        satellite: "Sentinel-2",
        cloudDetection: true,
        reconstruction: true,
        waterSegmentation: "SAM",
        metrics: true,
      },
      {
        id: 102,
        name: "Run #002",
        status: "completed",
        createdAt: "2026-08-16T08:15:00",
        satellite: "Sentinel-2",
        cloudDetection: false,
        reconstruction: true,
        waterSegmentation: "U-Net",
        metrics: true,
      },
      {
        id: 103,
        name: "Run #003",
        status: "running",
        createdAt: "2026-08-16T09:02:00",
        satellite: "Landsat-9",
        cloudDetection: true,
        reconstruction: false,
        waterSegmentation: "SAM",
        metrics: false,
      },
    ],
  },

  2: {
    projectId: 2,

    name: "Sume - Shapefile Original",

    location: "Sume, RN",

    description:
      "Projeto baseado no shapefile original da localidade.",

    shapefileImage: "/images/sume-original.png",

    cav: [
      {
        elevation: 180,
        area: 0,
        volume: 0,
      },
      {
        elevation: 181,
        area: 13000,
        volume: 6500,
      },
      {
        elevation: 182,
        area: 29000,
        volume: 26000,
      },
      {
        elevation: 183,
        area: 47000,
        volume: 63000,
      },
      {
        elevation: 184,
        area: 71000,
        volume: 121000,
      },
    ],

    realVolumes: [
      {
        date: "2026-01-15",
        elevation: 181.8,
        volume: 23500,
        source: "Medição de campo",
      },
      {
        date: "2026-03-18",
        elevation: 183.1,
        volume: 67000,
        source: "Medição de campo",
      },
    ],

    runs: [],
  },
};