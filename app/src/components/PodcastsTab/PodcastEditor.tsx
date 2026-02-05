import { CheckCircle2, Clock, Download, Loader2, Pause, Play, Save, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { usePodcastProject, usePodcasts } from '@/lib/hooks/usePodcasts';
import { useProfiles } from '@/lib/hooks/useProfiles';
import { cn } from '@/lib/utils/cn';

const SAMPLE_SCRIPT = `---
title: My First Podcast
episode: "Episode 1"
speakers:
  host1: "Sarah"
  guest1: "John"
description: "A conversation about AI and technology"
---

host1: Welcome to our podcast! Today we're discussing AI.

guest1: It's exciting to see how AI is changing our world.

host1: Absolutely, let's dive deeper into this topic.

guest1: I think the key is understanding both the opportunities and challenges.

[sound_effect: applause]

host1: Thank you for tuning in! See you next time.
`;

export function PodcastEditor() {
  const { projects } = usePodcasts();
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const { project, loading, error, startPipeline, pausePipeline, exportAudio } = usePodcastProject(
    selectedProjectId || '',
  );
  const { profiles } = useProfiles();

  const [scriptContent, setScriptContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Auto-select first project when available
  useEffect(() => {
    if (projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  // Load script when project is selected
  useEffect(() => {
    if (project && !isEditing) {
      setScriptContent(project.script_content);
    }
  }, [project, isEditing]);

  const handleSaveScript = async () => {
    if (!selectedProjectId || !project) return;

    setSaving(true);
    try {
      // TODO: Implement updateProject
      setIsEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleStartPipeline = async () => {
    if (!selectedProjectId) return;
    await startPipeline();
  };

  const handlePausePipeline = async () => {
    if (!selectedProjectId) return;
    await pausePipeline();
  };

  const handleExport = async () => {
    if (!selectedProjectId) return;
    await exportAudio();
  };

  const getSegmentStatusIcon = (segment: any) => {
    switch (segment.status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'generating':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getProfileName = (profileId: string | null) => {
    if (!profileId) return 'Unmapped';
    const profile = profiles.find((p) => p.id === profileId);
    return profile?.name || 'Unknown';
  };

  if (!selectedProjectId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted-foreground">Select a podcast project to edit</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-red-500">Failed to load project</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-semibold truncate">{project.name}</h1>
          {project.description && (
            <p className="text-sm text-muted-foreground mt-0.5 truncate">{project.description}</p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {project.pipeline_state === 'completed' && (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
          )}

          {project.pipeline_state === 'generating' ? (
            <Button variant="outline" size="sm" onClick={handlePausePipeline}>
              <Pause className="h-4 w-4 mr-1" />
              Pause
            </Button>
          ) : project.pipeline_state !== 'completed' ? (
            <Button variant="default" size="sm" onClick={handleStartPipeline}>
              <Play className="h-4 w-4 mr-1" />
              {project.pipeline_state === 'paused' ? 'Resume' : 'Start'}
            </Button>
          ) : null}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0 overflow-hidden flex">
        {/* Script Editor */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-border">
          <div className="flex items-center justify-between p-3 border-b border-border">
            <span className="text-sm font-medium">Script Editor</span>
            {isEditing && (
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button variant="default" size="sm" onClick={handleSaveScript} disabled={saving}>
                  {saving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-1" />
                  )}
                  Save
                </Button>
              </div>
            )}
          </div>
          <Textarea
            value={scriptContent}
            onChange={(e) => {
              setScriptContent(e.target.value);
              setIsEditing(true);
            }}
            placeholder={SAMPLE_SCRIPT}
            className="flex-1 resize-none font-mono text-sm leading-relaxed p-4"
          />
        </div>

        {/* Segments Panel */}
        <div className="w-80 flex flex-col min-w-0 bg-muted/20">
          <div className="p-3 border-b border-border">
            <span className="text-sm font-medium">Segments</span>
            <span className="text-xs text-muted-foreground ml-2">
              {project.completed_count}/{project.total_segments}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {project.segments.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center p-4">
                <p className="text-sm text-muted-foreground">No segments yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Edit and save the script to parse segments
                </p>
              </div>
            ) : (
              project.segments.map((segment) => (
                <div
                  key={segment.id}
                  className={cn(
                    'p-2 rounded-lg border border-border/50 bg-card/50',
                    'hover:border-border transition-colors',
                  )}
                >
                  {/* Segment Header */}
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-1.5">
                      {getSegmentStatusIcon(segment)}
                      <span className="text-xs font-medium">{segment.speaker}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {segment.segment_order + 1}
                    </Badge>
                  </div>

                  {/* Segment Text */}
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{segment.text}</p>

                  {/* Profile & Model Info */}
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>🎤 {getProfileName(segment.profile_id)}</span>
                    <span>•</span>
                    <span>🧠 {segment.model_size}</span>
                    {segment.error_message && (
                      <span className="text-red-500 ml-auto">Error: {segment.error_message}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
