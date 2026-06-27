import './Widgets.css';

const DRIVE_QUICK_ACTIONS = [
  {
    label: 'ORGANIZE MY DRIVE',
    prompt:
      'Organize my Google Drive. Start by listing all root-level files, then group them into logical folders (create new folders if needed) and move each file to the right place. Walk me through every action you take.',
  },
  {
    label: 'LIST ROOT FILES',
    prompt: 'List all the files and folders at the root of my Google Drive.',
  },
  {
    label: 'FIND A FILE',
    prompt: 'Search my Google Drive for ',
  },
];

function DriveWidget({ onQuickAction }) {
  return (
    <div className="widget glass-card glow-border drive-widget">
      <div className="widget-header">
        <span className="pixel-text widget-label">📁 DRIVE MANAGER</span>
      </div>

      <p className="drive-widget-hint">
        Ask me to organise your Drive, find files, or create folders — I'll handle the rest.
      </p>

      <div className="drive-action-list">
        {DRIVE_QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            className="drive-action-btn btn-pixel"
            onClick={() => onQuickAction(action.prompt)}
            title={action.prompt}
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default DriveWidget;
