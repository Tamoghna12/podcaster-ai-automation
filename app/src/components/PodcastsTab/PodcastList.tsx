import { formatDistanceToNow, formatDistanceToNow } from 'date-fns';
import { FileText, FileText, Plus, Plus, Trash2, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { usePodcasts } from '@/lib/hooks/usePodcasts';
import { cn } from '@/lib/utils/cn';
import { CreatePodcastDialog } from './CreatePodcastDialog';

export function PodcastList() {
  const { projects, loading, error, deleteProject, refetch } = usePodcasts();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const handleDelete = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project?')) return;

    setDeletingId(projectId);
    try {
      await deleteProject(projectId);
    } finally {
      setDeletingId(null);
    }
  };

  const handleCreateSuccess = () => {
    setCreateDialogOpen(false);
    refetch();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle':
        return 'text-muted-foreground';
      case 'generating':
        return 'text-blue-500';
      case 'paused':
        return 'text-yellow-500';
      case 'completed':
        return 'text-green-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-muted-foreground';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'idle':
        return 'bg-muted text-muted-foreground';
      case 'generating':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'paused':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'completed':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'error':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-red-500">Failed to load projects</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h2 className="text-lg font-semibold">Podcasts</h2>
        <span className="text-sm text-muted-foreground">{projects.length}</span>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-border" />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <FileText className="h-12 w-12 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground mb-2">No podcasts yet</p>
            <p className="text-xs text-muted-foreground">Create a new project to get started</p>
          </div>
        ) : (
          projects.map((project) => (
            <div
              key={project.id}
              className={cn(
                'p-3 rounded-lg border border-border/50 hover:border-border',
                'bg-card/50 hover:bg-card transition-colors cursor-pointer group',
                deletingId === project.id && 'opacity-50 pointer-events-none',
              )}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm truncate pr-2">{project.name}</h3>
                  {project.description && (
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                      {project.description}
                    </p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="opacity-0 group-hover:opacity-100 transition-opacity h-7 w-7 flex-shrink-0"
                  onClick={(e) => handleDelete(project.id, e)}
                  disabled={deletingId === project.id}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>

              {/* Status & Progress */}
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={cn(
                    'text-xs px-2 py-0.5 rounded-full border',
                    getStatusBadge(project.pipeline_state),
                  )}
                >
                  {project.pipeline_state}
                </span>
                {project.pipeline_state !== 'idle' && project.total_segments > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {project.completed_count} / {project.total_segments}
                  </span>
                )}
              </div>

              {/* Timestamp */}
              <div className="mt-2 text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Button */}
      <div className="p-4 border-t border-border">
        <Button
          variant="outline"
          className="w-full justify-start gap-2"
          onClick={() => setCreateDialogOpen(true)}
        >
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      <CreatePodcastDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} />
    </div>
  );
}
