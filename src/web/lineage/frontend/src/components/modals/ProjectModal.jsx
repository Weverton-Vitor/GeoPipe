import { useState } from "react";

const emptyProject = {
  name: "",
  location: "",
  description: "",
  shapefile: null,
  elevationFile: null,
  volumeFile: null,
};

function getInitialForm(project) {
  if (!project) {
    return emptyProject;
  }

  return {
    name: project.name || "",
    location: project.location || "",
    description: project.description || "",
    shapefile: null,
    elevationFile: null,
    volumeFile: null,
  };
}

export default function ProjectModal({
  project,
  onClose,
  onSave,
}) {
  const [form, setForm] = useState(() =>
    getInitialForm(project)
  );

  function handleChange(event) {
    const { name, value, files } = event.target;

    setForm((current) => ({
      ...current,
      [name]: files ? files[0] : value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (!form.name.trim() || !form.location.trim()) {
      return;
    }

    onSave(form);
  }

  const isEditing = Boolean(project);

  return (
    <div
      className="modal-overlay"
      onMouseDown={onClose}
    >
      <div
        className="modal"
        onMouseDown={(event) =>
          event.stopPropagation()
        }
      >
        <div className="modal-header">
          <div>
            <span className="header-eyebrow">
              {isEditing
                ? "EDITAR PROJETO"
                : "NOVO PROJETO"}
            </span>

            <h2>
              {isEditing
                ? "Editar projeto"
                : "Criar novo projeto"}
            </h2>
          </div>

          <button
            className="modal-close"
            onClick={onClose}
            type="button"
            aria-label="Fechar"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h3>Informações gerais</h3>

            <div className="form-grid">
              <label>
                Nome do projeto *
                <input
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="Ex.: Sume - ROI Quadrada"
                />
              </label>

              <label>
                Localidade *
                <input
                  name="location"
                  value={form.location}
                  onChange={handleChange}
                  placeholder="Ex.: Sume, RN"
                />
              </label>

              <label className="full-width">
                Descrição
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Descreva brevemente o projeto..."
                  rows="3"
                />
              </label>
            </div>
          </div>

          <div className="form-section">
            <h3>Arquivos do projeto</h3>

            <div className="file-fields">
              <label>
                Shapefile

                <div className="file-input">
                  <span>◇</span>

                  <input
                    type="file"
                    name="shapefile"
                    accept=".shp,.zip,.geojson"
                    onChange={handleChange}
                  />

                  <span className="file-name">
                    {form.shapefile
                      ? form.shapefile.name
                      : "Selecionar arquivo"}
                  </span>
                </div>
              </label>

              <label>
                Arquivo de cotas

                <div className="file-input">
                  <span>◇</span>

                  <input
                    type="file"
                    name="elevationFile"
                    accept=".csv,.txt"
                    onChange={handleChange}
                  />

                  <span className="file-name">
                    {form.elevationFile
                      ? form.elevationFile.name
                      : "Selecionar arquivo"}
                  </span>
                </div>
              </label>

              <label>
                Volume medido in loco

                <div className="file-input">
                  <span>◇</span>

                  <input
                    type="file"
                    name="volumeFile"
                    accept=".csv,.txt"
                    onChange={handleChange}
                  />

                  <span className="file-name">
                    {form.volumeFile
                      ? form.volumeFile.name
                      : "Selecionar arquivo"}
                  </span>
                </div>
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
            >
              Cancelar
            </button>

            <button
              type="submit"
              className="primary-button"
            >
              {isEditing
                ? "Salvar alterações"
                : "Criar projeto"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}