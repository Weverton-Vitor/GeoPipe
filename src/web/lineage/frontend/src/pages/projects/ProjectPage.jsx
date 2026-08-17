import { useNavigate, useParams } from "react-router-dom";

import Sidebar from "../../components/layout/Sidebar";
import Header from "../../components/layout/Header";

import ProjectOverview from "../../components/projects/ProjectOverview";

import { projectDetails } from "../../mocks/projectDetails";

import styles from "./ProjectPage.module.css";


export default function ProjectPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();


  const project = projectDetails[projectId];

  if (!project) {
    return (
      <div className={styles.app}>
        <Sidebar />

        <main className={styles.main}>
          <Header />

          <div className={styles.notFound}>
            <h2>Projeto não encontrado</h2>

            <p>
              O projeto solicitado não existe ou foi removido.
            </p>

            <button
              onClick={() => navigate("/")}
              className={styles.backButton}
            >
              ← Voltar para projetos
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.app}>
      <Sidebar />

      <main className={styles.main}>
        <Header />

        <div className={styles.content}>
          <button
            className={styles.backButton}
            onClick={() => navigate("/")}
          >
            ← Voltar para projetos
          </button>

          <ProjectOverview project={project} />
        </div>
      </main>
    </div>
  );
}