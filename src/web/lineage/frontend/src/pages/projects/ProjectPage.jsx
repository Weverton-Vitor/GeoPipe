import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Sidebar from "../../components/layout/Sidebar";
import Header from "../../components/layout/Header";
import ProjectOverview from "../../components/projects/ProjectOverview";

import { getProject } from "../../api/geopipeApi";

import styles from "./ProjectPage.module.css";


export default function ProjectPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {
    async function loadProject() {
      try {
        setLoading(true);
        setError(null);

        const data = await getProject(projectId);

        setProject(data);
      } catch (error) {
        console.error("Erro ao carregar projeto:", error);

        setProject(null);
        setError(error);
      } finally {
        setLoading(false);
      }
    }

    if (projectId) {
      loadProject();
    }
  }, [projectId]);


  // ==========================================
  // LOADING
  // ==========================================

  if (loading) {
    return (
      <div className={styles.app}>
        <Sidebar />

        <main className={styles.main}>
          <Header />

          <div className={styles.notFound}>
            <h2>Carregando projeto...</h2>
            <p>
              Aguarde enquanto buscamos os dados do projeto.
            </p>
          </div>
        </main>
      </div>
    );
  }


  // ==========================================
  // PROJETO NÃO ENCONTRADO
  // ==========================================

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


  // ==========================================
  // PROJETO
  // ==========================================

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
