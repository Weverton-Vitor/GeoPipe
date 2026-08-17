export default function ProjectCard({
  project,
  onEdit,
  onDelete,
  onOpen,
}) {
  return (
    <article className="project-card">
      <div className="project-card-top">
        <div className="project-icon">⌁</div>

        <button className="card-menu" type="button">
          ⋮
        </button>
      </div>

      <div className="project-card-content">
        <div className="project-location">
          <span>●</span>
          {project.location}
        </div>

        <h2>{project.name}</h2>

        <p>{project.description}</p>
      </div>

      <div className="project-stats">
        <div>
          <span>Runs</span>
          <strong>{project.runs}</strong>
        </div>

        <div>
          <span>Shapefile</span>
          <strong title={project.shapefile}>
            {project.shapefile}
          </strong>
        </div>
      </div>

      <div className="project-card-footer">
        <span className="updated">
          Atualizado em{" "}
          {new Date(project.updatedAt).toLocaleDateString("pt-BR")}
        </span>

        <div className="card-actions">
          <button
            className="icon-button"
            onClick={() => onEdit(project)}
            title="Editar projeto"
          >
            ✎
          </button>

          <button
            className="icon-button danger"
            onClick={() => onDelete(project)}
            title="Excluir projeto"
          >
            ×
          </button>

          <button
            className="open-button"
            onClick={() => onOpen(project)}
          >
            Abrir projeto →
          </button>
        </div>
      </div>
    </article>
  );
}