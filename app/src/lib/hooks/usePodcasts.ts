import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '@/lib/api/client';
import type { PodcastProject, PodcastProjectCreate, PodcastSegmentUpdate } from '@/lib/api/types';

interface PodcastProgressEvent {
  type: 'progress' | 'segment_complete' | 'segment_failed' | 'complete' | 'error';
  data?: any;
}

export function usePodcasts() {
  const [projects, setProjects] = useState<PodcastProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<Array<PodcastProject>>('/podcast/projects');
      setProjects(response.data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  const createProject = useCallback(
    async (data: PodcastProjectCreate) => {
      const formData = new FormData();
      formData.append('script_content', data.script_content);

      const response = await apiClient.post<PodcastProject>('/podcast/projects', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      await fetchProjects();
      return response.data;
    },
    [fetchProjects],
  );

  const deleteProject = useCallback(
    async (projectId: string) => {
      await apiClient.delete(`/podcast/projects/${projectId}`);
      await fetchProjects();
    },
    [fetchProjects],
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return {
    projects,
    loading,
    error,
    refetch: fetchProjects,
    createProject,
    deleteProject,
  };
}

export function usePodcastProject(projectId: string) {
  const [project, setProject] = useState<PodcastProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const fetchProject = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PodcastProject>(`/podcast/projects/${projectId}`);
      setProject(response.data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const updateProject = useCallback(
    async (data: Partial<PodcastProjectCreate>) => {
      if (!project) return;

      const formData = new FormData();
      if (data.script_content !== undefined) {
        formData.append('script_content', data.script_content);
      }

      const response = await apiClient.put<PodcastProject>(
        `/podcast/projects/${projectId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );

      setProject(response.data);
      return response.data;
    },
    [project, projectId],
  );

  const updateSegment = useCallback(
    async (segmentId: string, data: PodcastSegmentUpdate) => {
      const response = await apiClient.put<PodcastSegment>(
        `/podcast/projects/${projectId}/segments/${segmentId}`,
        data,
      );

      if (project) {
        setProject({
          ...project,
          segments: project.segments.map((s) => (s.id === segmentId ? response.data : s)),
        });
      }

      return response.data;
    },
    [project, projectId],
  );

  const startPipeline = useCallback(async () => {
    try {
      const response = await apiClient.post<{ project_id: string; state: string }>(
        `/podcast/projects/${projectId}/start`,
      );

      setIsGenerating(true);
      await fetchProject();
      return response.data;
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, [projectId, fetchProject]);

  const pausePipeline = useCallback(async () => {
    try {
      await apiClient.post(`/podcast/projects/${projectId}/pause`);
      setIsGenerating(false);
      await fetchProject();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, [projectId, fetchProject]);

  const exportAudio = useCallback(async () => {
    const response = await apiClient.post<Blob>(
      `/podcast/projects/${projectId}/export`,
      {},
      { responseType: 'blob' },
    );

    // Download file
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `podcast-${projectId}.wav`;
    link.click();
    window.URL.revokeObjectURL(url);

    return response.data;
  }, [projectId]);

  // Subscribe to SSE progress stream
  useEffect(() => {
    if (!projectId) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`/podcast/projects/${projectId}/progress`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as PodcastProgressEvent;

        if (data.type === 'progress') {
          // Update project with progress info
          if (project && data.data) {
            setProject({
              ...project,
              pipeline_state: data.data.pipeline_state,
              current_segment_index: data.data.current_segment_index,
              completed_count: data.data.completed_count,
              failed_count: data.data.failed_count,
              total_segments: data.data.total_segments,
            });
          }
        } else if (data.type === 'segment_complete' || data.type === 'segment_failed') {
          // Refetch project to get updated segments
          fetchProject();
        } else if (data.type === 'complete') {
          setIsGenerating(false);
          fetchProject();
        } else if (data.type === 'error') {
          setIsGenerating(false);
          setError(new Error(data.data?.error || 'Pipeline error'));
          fetchProject();
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [projectId, project, fetchProject]);

  // Update isGenerating based on project state
  useEffect(() => {
    if (project) {
      setIsGenerating(project.pipeline_state === 'generating');
    }
  }, [project]);

  useEffect(() => {
    if (projectId) {
      fetchProject();
    }
  }, [projectId, fetchProject]);

  return {
    project,
    loading,
    error,
    isGenerating,
    refetch: fetchProject,
    updateProject,
    updateSegment,
    startPipeline,
    pausePipeline,
    exportAudio,
  };
}

import type { PodcastSegment } from '@/lib/api/types';
