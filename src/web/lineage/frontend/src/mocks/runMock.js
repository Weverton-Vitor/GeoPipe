export const runMock = {
  id: 24,

  name: "Processamento Agosto 2026",

  project: {
    id: 1,
    name: "Sume - ROI Quadrada",
    location: "Sume, RN",
  },

  year: 2026,

  status: "running",

  startedAt: "16/08/2026 14:32",

  elapsedTime: "02:34",

  currentStage: "reconstruction",

  progress: {
    current: 37,
    total: 52,
    percentage: 71,
  },

  configuration: {
    download: {
      method: "sentinel-2",
    },

    cloudDetection: {
      enabled: true,
      method: "s2cloudless",
    },

    reconstruction: {
      enabled: true,
      method: "interpolation",
    },

    waterSegmentation: {
      method: "sam",
    },
  },

  stages: [
    {
      id: "download",
      number: "01",
      name: "Download",
      status: "completed",
      method: "Sentinel-2",

      artifacts: [
        {
          id: 101,
          type: "image",
          role: "output",
          name: "IMG_20260812_RGB",
          url: "/mock/images/rgb-original.png",
        },
      ],
    },

    {
      id: "cloud_detection",
      number: "02",
      name: "Detecção de nuvens",
      status: "completed",
      method: "S2Cloudless",

      artifacts: [
        {
          id: 201,
          type: "image",
          role: "input",
          name: "Imagem RGB",
          url: "/mock/images/rgb-original.png",
        },
        {
          id: 202,
          type: "mask",
          role: "output",
          name: "Máscara de nuvens",
          url: "/mock/images/cloud-mask.png",
        },
      ],
    },

    {
      id: "reconstruction",
      number: "03",
      name: "Reconstrução",
      status: "running",
      method: "Interpolation",

      artifacts: [
        {
          id: 301,
          type: "image",
          role: "input",
          name: "Imagem com nuvens",
          url: "/mock/images/rgb-original.png",
        },
      ],
    },

    {
      id: "water_segmentation",
      number: "04",
      name: "Segmentação de água",
      status: "pending",
      method: "SAM",

      artifacts: [],
    },

    {
      id: "volume",
      number: "05",
      name: "Cálculo do volume",
      status: "pending",
      method: "Modelo CAV",

      artifacts: [],
      result: null,
    },

    {
      id: "metrics",
      number: "06",
      name: "Métricas",
      status: "pending",
      method: "Comparação com referência",

      artifacts: [],
      metrics: [],
    },
  ],
};