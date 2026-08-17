import { useState } from "react";

import styles from "./NewRunModal.module.css";

const initialForm = {
    name: "",
    year: new Date().getFullYear(),

    download: {
        method: "sentinel-2",
    },

    cloudDetection: {
        enabled: true,
        method: "s2cloudless",
    },

    reconstruction: {
        enabled: false,
        method: "interpolation",
    },

    waterSegmentation: {
        method: "sam",
    },
};

export default function NewRunModal({
    project,
    onClose,
    onCreate,
}) {
    const [form, setForm] = useState(initialForm);

    function updateField(section, field, value) {
        setForm((current) => ({
            ...current,

            [section]: {
                ...current[section],
                [field]: value,
            },
        }));
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (!form.name.trim()) {
            return;
        }

        onCreate({
            ...form,

            year: Number(form.year),
        });
    }

    return (
        <div
            className={styles.overlay}
            onMouseDown={onClose}
        >
            <div
                className={styles.modal}
                onMouseDown={(event) =>
                    event.stopPropagation()
                }
            >
                <header className={styles.header}>
                    <div>
                        <span className={styles.eyebrow}>
                            NOVA RUN
                        </span>

                        <h2>Criar nova run</h2>

                        <p>
                            Configure os métodos que serão utilizados
                            no processamento.
                        </p>
                    </div>

                    <button
                        type="button"
                        className={styles.close}
                        onClick={onClose}
                        aria-label="Fechar"
                    >
                        ×
                    </button>
                </header>

                <form
                    className={styles.form}
                    onSubmit={handleSubmit}
                >
                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <div>
                                <span className={styles.sectionNumber}>
                                    01
                                </span>

                                <div>
                                    <h3>Informações da run</h3>

                                    <p>
                                        Identificação e período do
                                        processamento.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className={styles.grid}>
                            <label className={styles.field}>
                                <span>Nome da run *</span>

                                <input
                                    value={form.name}
                                    onChange={(event) =>
                                        setForm((current) => ({
                                            ...current,
                                            name: event.target.value,
                                        }))
                                    }
                                    placeholder="Ex.: Processamento Agosto 2026"
                                />
                            </label>

                        </div>

                        <div className={styles.projectInfo}>
                            <span>Projeto</span>

                            <strong>{project.name}</strong>

                            <small>{project.location}</small>
                        </div>
                    </section>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <div>
                                <span className={styles.sectionNumber}>
                                    02
                                </span>

                                <div>
                                    <h3>Download</h3>

                                    <p>
                                        Fonte das imagens utilizadas no
                                        processamento.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className={styles.methodGrid}>
                            <MethodOption
                                title="Sentinel-2"
                                description="Imagens multiespectrais"
                                selected={
                                    form.download.method ===
                                    "sentinel-2"
                                }
                                onClick={() =>
                                    updateField(
                                        "download",
                                        "method",
                                        "sentinel-2"
                                    )
                                }
                            />

                            <MethodOption
                                title="Landsat-9"
                                description="Imagens Landsat"
                                selected={
                                    form.download.method ===
                                    "landsat-9"
                                }
                                onClick={() =>
                                    updateField(
                                        "download",
                                        "method",
                                        "landsat-9"
                                    )
                                }
                            />
                        </div>
                        <div>
                            <label className={styles.field}>
                                <span>Data Inicial</span>

                                <input
                                    type="date"
                                    min="2017-01-01"
                                    onChange={(event) =>
                                        setForm((current) => ({
                                            ...current,
                                            year: event.target.value,
                                        }))
                                    }
                                />
                            </label>
                            <label className={styles.field}>
                                <span>Data Final</span>

                                <input
                                    type="date"
                                    min="2017-01-01"
                                    onChange={(event) =>
                                        setForm((current) => ({
                                            ...current,
                                            year: event.target.value,
                                        }))
                                    }
                                />
                            </label>
                        </div>
                    </section>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <div>
                                <span className={styles.sectionNumber}>
                                    03
                                </span>

                                <div>
                                    <h3>Detecção de nuvens</h3>

                                    <p>
                                        Etapa opcional para identificação
                                        e remoção de nuvens.
                                    </p>
                                </div>
                            </div>

                            <Toggle
                                checked={
                                    form.cloudDetection.enabled
                                }
                                onChange={(value) =>
                                    updateField(
                                        "cloudDetection",
                                        "enabled",
                                        value
                                    )
                                }
                            />
                        </div>

                        {form.cloudDetection.enabled && (
                            <div className={styles.methodGrid}>

                                <MethodOption
                                    title="S2Cloudless"
                                    description="Detecção baseada em probabilidade"
                                    selected={
                                        form.cloudDetection.method ===
                                        "s2cloudless"
                                    }
                                    onClick={() =>
                                        updateField(
                                            "cloudDetection",
                                            "method",
                                            "s2cloudless"
                                        )
                                    }
                                />

                                <MethodOption
                                    title="FMask"
                                    description="Detecção baseada em probabilidade"
                                    selected={
                                        form.cloudDetection.method ===
                                        "fmask"
                                    }
                                    onClick={() =>
                                        updateField(
                                            "fmask",
                                            "method",
                                            "fmask"
                                        )
                                    }
                                />

                                <MethodOption
                                    title="Modelo customizado"
                                    description="Modelo ONNX do projeto"
                                    selected={
                                        form.cloudDetection.method ===
                                        "custom"
                                    }
                                    onClick={() =>
                                        updateField(
                                            "cloudDetection",
                                            "method",
                                            "custom"
                                        )
                                    }
                                />
                            </div>
                        )}
                    </section>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <div>
                                <span className={styles.sectionNumber}>
                                    04
                                </span>

                                <div>
                                    <h3>Reconstrução</h3>

                                    <p>
                                        Reconstrução das imagens após o
                                        tratamento.
                                    </p>
                                </div>
                            </div>

                            <Toggle
                                checked={
                                    form.reconstruction.enabled
                                }
                                onChange={(value) =>
                                    updateField(
                                        "reconstruction",
                                        "enabled",
                                        value
                                    )
                                }
                            />
                        </div>

                        {form.reconstruction.enabled && (
                            <div className={styles.methodGrid}>
                                <MethodOption
                                    title="Interpolation"
                                    description="Reconstrução por interpolação"
                                    selected={
                                        form.reconstruction.method ===
                                        "interpolation"
                                    }
                                    onClick={() =>
                                        updateField(
                                            "reconstruction",
                                            "method",
                                            "interpolation"
                                        )
                                    }
                                />

                                <MethodOption
                                    title="Modelo customizado"
                                    description="Modelo de reconstrução"
                                    selected={
                                        form.reconstruction.method ===
                                        "custom"
                                    }
                                    onClick={() =>
                                        updateField(
                                            "reconstruction",
                                            "method",
                                            "custom"
                                        )
                                    }
                                />
                            </div>
                        )}
                    </section>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <div>
                                <span className={styles.sectionNumber}>
                                    05
                                </span>

                                <div>
                                    <h3>Segmentação de água</h3>

                                    <p>
                                        Método utilizado para gerar a
                                        máscara de água.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className={styles.methodGrid}>
                            <MethodOption
                                title="Vgg-Unet"
                                description="Vgg-Unet"
                                selected={
                                    form.waterSegmentation.method ===
                                    "vggunet"
                                }
                                onClick={() =>
                                    updateField(
                                        "waterSegmentation",
                                        "method",
                                        "vggunet"
                                    )
                                }
                            />

                            <MethodOption
                                title="Deepwatermap"
                                description="Modelo de segmentação Deepwatermap"
                                selected={
                                    form.waterSegmentation.method ===
                                    "deepwatermap"
                                }
                                onClick={() =>
                                    updateField(
                                        "waterSegmentation",
                                        "method",
                                        "deepwatermap"
                                    )
                                }
                            />

                            <MethodOption
                                title="WatNet"
                                description="Modelo de segmentação WatNet"
                                selected={
                                    form.waterSegmentation.method ===
                                    "watNet"
                                }
                                onClick={() =>
                                    updateField(
                                        "waterSegmentation",
                                        "method",
                                        "watNet"
                                    )
                                }

                            /><MethodOption
                                title="NDWI"
                                description="Modelo de segmentação NDWI"
                                selected={
                                    form.waterSegmentation.method ===
                                    "ndwi"
                                }
                                onClick={() =>
                                    updateField(
                                        "waterSegmentation",
                                        "method",
                                        "ndwi"
                                    )
                                }
                            /><MethodOption
                                title="MNDWI"
                                description="Modelo de segmentação MNDWI"
                                selected={
                                    form.waterSegmentation.method ===
                                    "mndwi"
                                }
                                onClick={() =>
                                    updateField(
                                        "waterSegmentation",
                                        "method",
                                        "mndwi"
                                    )
                                }
                            />
                        </div>
                    </section>

                    <section className={styles.summary}>
                        <div>
                            <span className={styles.eyebrow}>
                                CONFIGURAÇÃO
                            </span>

                            <strong>
                                Pronto para iniciar
                            </strong>

                            <p>
                                A run será criada com a configuração
                                selecionada. O processamento será
                                iniciado posteriormente.
                            </p>
                        </div>

                        <div className={styles.summarySteps}>
                            <SummaryStep
                                label="Download"
                                value={form.download.method}
                            />

                            <SummaryStep
                                label="Nuvens"
                                value={
                                    form.cloudDetection.enabled
                                        ? form.cloudDetection.method
                                        : "Desativado"
                                }
                            />

                            <SummaryStep
                                label="Reconstrução"
                                value={
                                    form.reconstruction.enabled
                                        ? form.reconstruction.method
                                        : "Desativado"
                                }
                            />

                            <SummaryStep
                                label="Água"
                                value={
                                    form.waterSegmentation.method
                                }
                            />
                        </div>
                    </section>

                    <footer className={styles.footer}>
                        <button
                            type="button"
                            className={styles.cancel}
                            onClick={onClose}
                        >
                            Cancelar
                        </button>

                        <button
                            type="submit"
                            className={styles.create}
                        >
                            Criar run
                        </button>
                    </footer>
                </form>
            </div>
        </div>
    );
}

function MethodOption({
    title,
    description,
    selected,
    onClick,
}) {
    return (
        <button
            type="button"
            className={`${styles.method} ${selected ? styles.selected : ""
                }`}
            onClick={onClick}
        >
            <span className={styles.radio}>
                {selected && <span />}
            </span>

            <span className={styles.methodContent}>
                <strong>{title}</strong>

                <small>{description}</small>
            </span>
        </button>
    );
}

function Toggle({ checked, onChange }) {
    return (
        <button
            type="button"
            className={`${styles.toggle} ${checked ? styles.toggleActive : ""
                }`}
            onClick={() => onChange(!checked)}
            aria-pressed={checked}
        >
            <span />
        </button>
    );
}

function SummaryStep({ label, value }) {
    return (
        <div className={styles.summaryStep}>
            <span>{label}</span>

            <strong>{value}</strong>
        </div>
    );
}