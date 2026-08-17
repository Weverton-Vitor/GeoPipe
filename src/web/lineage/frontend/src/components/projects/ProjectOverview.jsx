import CavTable from "./CavTable";
import RealVolumesTable from "./RealVolumesTable";
import RunCard from "../cards/RunCard";

import { useState } from "react";

import NewRunModal from "../modals/NewRunModal";


import styles from "./ProjectOverview.module.css";

export default function ProjectOverview({ project }) {
    const [newRunModalOpen, setNewRunModalOpen] = useState(false);

    return (
        <div className={styles.container}>
            <section className={styles.projectHeader}>
                <div>
                    <div className={styles.location}>
                        <span>●</span>

                        {project.location}
                    </div>

                    <h1>{project.name}</h1>

                    <p>{project.description}</p>
                </div>

                <button
                    className={styles.runButton}
                    onClick={() => setNewRunModalOpen(true)}
                >
                    + Nova runn
                </button>
            </section>

            <section className={styles.mapSection}>
                <div className={styles.sectionHeader}>
                    <div>
                        <span className={styles.eyebrow}>
                            ÁREA DO PROJETO
                        </span>

                        <h2>Shapefile</h2>
                    </div>

                    <span className={styles.fileName}>
                        ROI / shapefile
                    </span>
                </div>

                <div className={styles.mapContainer}>
                    <img
                        src={project.shapefileImage}
                        alt={`Shapefile do projeto ${project.name}`}
                    />
                </div>
            </section>

            <section className={styles.dataGrid}>
                <div className={styles.dataSection}>
                    <div className={styles.sectionHeader}>
                        <div>
                            <span className={styles.eyebrow}>
                                DADOS DO RESERVATÓRIO
                            </span>

                            <h2>Curva CAV</h2>
                        </div>
                    </div>

                    <CavTable data={project.cav} />
                </div>

                <div className={styles.dataSection}>
                    <div className={styles.sectionHeader}>
                        <div>
                            <span className={styles.eyebrow}>
                                DADOS DE CAMPO
                            </span>

                            <h2>Volumes reais</h2>
                        </div>
                    </div>

                    <RealVolumesTable data={project.realVolumes} />
                </div>
            </section>

            <section className={styles.runsSection}>
                <div className={styles.runsHeader}>
                    <div>
                        <span className={styles.eyebrow}>
                            PROCESSAMENTOS
                        </span>

                        <h2>Runs</h2>

                        <p>
                            Processamentos executados neste projeto.
                        </p>
                    </div>

                    <span className={styles.runCount}>
                        {project.runs.length}{" "}
                        {project.runs.length === 1
                            ? "run"
                            : "runs"}
                    </span>
                </div>

                <div className={styles.runsList}>
                    {project.runs.length > 0 ? (
                        project.runs.map((run) => (
                            <RunCard
                                key={run.id}
                                run={run}
                            />
                        ))
                    ) : (
                        <div className={styles.emptyRuns}>
                            <strong>Nenhuma run executada</strong>

                            <span>
                                Crie a primeira run para começar o
                                processamento deste projeto.
                            </span>

                            <button
                                className={styles.runButton}
                                onClick={() => setNewRunModalOpen(true)}
                            >
                                + Nova run
                            </button>
                        </div>
                    )}
                </div>
            </section>

            {newRunModalOpen && (
                <NewRunModal
                    project={project}
                    onClose={() => setNewRunModalOpen(false)}
                    onCreate={(configuration) => {
                        console.log("Nova run:", configuration);

                        setNewRunModalOpen(false);
                    }}
                />
            )}
        </div>
    );
}