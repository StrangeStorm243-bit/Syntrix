interface ProjectSelectorProps {
  projects: { id: string; name: string }[];
  activeProject: string | null;
  onChange: (id: string) => void;
}

export function ProjectSelector({ projects, activeProject, onChange }: ProjectSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs font-medium text-gray-400">Project</label>
      <select
        value={activeProject || ''}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-gray-600 bg-gray-800 px-3 py-1.5 text-sm text-white"
      >
        {projects.length === 0 ? (
          <option value="">No projects</option>
        ) : (
          projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))
        )}
      </select>
    </div>
  );
}
