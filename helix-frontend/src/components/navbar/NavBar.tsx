import './NavBar.css';
type ActiveView = 'workspace' | 'documents';

interface NavBarProps {
  onNewSession: () => void;
  currentSessionId: number | null;
  activeView: ActiveView;
  onShowWorkspace: () => void;
  onShowDocuments: () => void;
}

function NavBar({
  onNewSession,
  currentSessionId,
  activeView,
  onShowWorkspace,
  onShowDocuments
}: NavBarProps) {


  return (
    <header className="navbar-header">
      <div className="navbar-container">
        <div className="navbar-brand">
          <div className="logo">
            <span className="logo-text">Helix</span>
          </div>

          <div className="session-indicator">
            {currentSessionId ? (
              <div className="session-badge">
                <span className="session-label">Session</span>
                <span className="session-number">{currentSessionId}</span>
              </div>
            ) : (
              <div className="no-session-badge">No active session</div>
            )}
          </div>
        </div>


        <nav className="navbar-nav"> 
          <div className="view-switcher">
            <button
              onClick={onShowWorkspace}
              className={`nav-button ${activeView === 'workspace' ? 'active' : ''}`}
            >
              <span className="nav-icon workspace-icon"></span>
              <span className="nav-text">Workspace</span>
            </button>

            <button
              onClick={onShowDocuments}
              className={`nav-button ${activeView === 'documents' ? 'active' : ''}`}
            >
              <span className="nav-icon documents-icon"></span>
              <span className="nav-text">Documents</span>
            </button>
          </div>

          <button
            onClick={onNewSession}
            className="nav-button action-button"
          >
            <span className="button-icon new-icon"></span>
            <span className="button-text">
              {currentSessionId ? 'New Session' : 'Start Session'}
            </span>
          </button>
        </nav>
      </div>
    </header>
  );
}

export default NavBar;