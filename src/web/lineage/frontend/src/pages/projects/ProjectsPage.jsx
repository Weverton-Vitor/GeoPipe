import { useEffect, useMemo, useState } from "react";

import Sidebar from "../../components/layout/Sidebar";
import Header from "../../components/layout/Header";
import ProjectCard from "../../components/cards/ProjectCard";
import ProjectModal from "../../components/modals/ProjectModal";

import { useNavigate } from "react-router-dom";

import {
  createProject,
  getProjects,
} from "../../api/geopipeApi";

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  // ==========================================
  // CARREGAR PROJETOS
  // ==========================================

  useEffect(() => {
    async function loadProjects() {
      try {
        setLoading(true);

        const data = await getProjects();

        setProjects(data);
      } catch (error) {
        console.error("Erro ao carregar projetos:", error);
        alert("Não foi possível carregar os projetos.");
      } finally {
        setLoading(false);
      }
    }

    loadProjects();
  }, []);

  // ==========================================
  // FILTRO
  // ==========================================

  const filteredProjects = useMemo(() => {
    const term = search.toLowerCase().trim();

    if (!term) {
      return projects;
    }

    return projects.filter((project) => {
      return (
        project.name.toLowerCase().includes(term) ||
        project.location.toLowerCase().includes(term)
      );
    });
  }, [projects, search]);

  // ==========================================
  // CRIAR
  // ==========================================

  function handleCreate() {
    setEditingProject(null);
    setModalOpen(true);
  }

  // ==========================================
  // EDITAR
  // ==========================================

  function handleEdit(project) {
    setEditingProject(project);
    setModalOpen(true);
  }

  // ==========================================
  // EXCLUIR
  // ==========================================

  function handleDelete(project) {
    const confirmed = window.confirm(
      `Deseja realmente excluir o projeto "${project.name}"?`
    );

    if (!confirmed) {
      return;
    }

    // Por enquanto continua apenas local.
    setProjects((current) =>
      current.filter((item) => item.id !== project.id)
    );
  }

  // ==========================================
  // SALVAR
  // ==========================================

  async function handleSave(form) {
    try {
      if (editingProject) {
        // Por enquanto, mantém a lógica local para edição.
        setProjects((current) =>
          current.map((project) =>
            project.id === editingProject.id
              ? {
                  ...project,
                  ...form,
                  updated_at: new Date()
                    .toISOString()
                    .split("T")[0],
                }
              : project
          )
        );
      } else {
        const newProject = await createProject(form);

        setProjects((current) => [
          newProject,
          ...current,
        ]);
      }

      setModalOpen(false);
      setEditingProject(null);
    } catch (error) {
      console.error("Erro ao salvar projeto:", error);
      alert("Não foi possível salvar o projeto.");
    }
  }

  // ==========================================
  // ABRIR
  // ==========================================

  function handleOpen(project) {
    navigate(`/projects/${project.id}`);
  }

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <div className="app">
      <Sidebar />

      <main className="main">
        <Header />

        <div className="content">
          <div className="page-intro">
            <div>
              <h2>Seus projetos</h2>

              <p>
                Gerencie localidades, arquivos e configurações
                dos seus projetos GeoPipe.
              </p>
            </div>

            <button
              className="primary-button"
              onClick={handleCreate}
            >
              <span>+</span>
              Novo projeto
            </button>
          </div>

          <div className="toolbar">
            <div className="search-box">
              <span>⌕</span>

              <input
                type="text"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Buscar por projeto ou localidade..."
              />
            </div>

            <button className="filter-button">
              ☷ Filtros
            </button>

            <span className="project-count">
              {filteredProjects.length}{" "}
              {filteredProjects.length === 1
                ? "projeto"
                : "projetos"}
            </span>
          </div>

          {loading ? (
            <div className="empty-state">
              <h3>Carregando projetos...</h3>
            </div>
          ) : filteredProjects.length > 0 ? (
            <div className="projects-grid">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onOpen={handleOpen}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">⌕</div>

              <h3>Nenhum projeto encontrado</h3>

              <p>
                Tente buscar por outro nome ou crie um novo
                projeto.
              </p>

              <button
                className="primary-button"
                onClick={handleCreate}
              >
                Criar projeto
              </button>
            </div>
          )}
        </div>
      </main>

      {modalOpen && (
        <ProjectModal
          project={editingProject}
          onClose={() => {
            setModalOpen(false);
            setEditingProject(null);
          }}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
