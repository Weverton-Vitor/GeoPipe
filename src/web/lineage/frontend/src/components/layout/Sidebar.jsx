export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
          
          <img
          src="/geopipe_icon.png"
          alt="Geopipe Logo"
          style={{ width: '45px', height: '45px' }}
        />

        <div>
          <strong>GeoPipe</strong>
          <span>Pipeline Manager</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <a className="nav-item active" href="#">
          <span>▦</span>
          Projetos
        </a>

        <a className="nav-item" href="#">
          <span>◌</span>
          Runs
        </a>
      </nav>

      <div className="sidebar-bottom">
        <a className="nav-item" href="#">
          <span>⚙</span>
          Configurações
        </a>
      </div>
    </aside>
  );
}