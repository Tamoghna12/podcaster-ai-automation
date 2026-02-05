import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api/client';
import type { PodcastProject, PodcastProjectCreate, PodcastSegmentUpdate } from '@/lib/api/types';

export function usePodcasts() {
  const [projects, setProjects] = useState<PodcastProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchProjects = async () => {
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
  };

  const createProject = async (data: PodcastProjectCreate) => {
    const formData = new FormData();
    formData.append('script_content', data.script_content);

    const response = await apiClient.post<PodcastProject>('/podcast/projects', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    setProjects((prev) => [...prev, response.data]);
    return response.data;
  };

  const deleteProject = async (projectId: string) => {
    await apiClient.delete(`/podcast/projects/${projectId}`);
    setProjects((prev) => prev.filter((p) => p.id !== projectId));
  };

  useEffect(() => {
    fetchProjects();
  }, []);

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

  const fetchProject = async () => {
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
  };

  const updateProject = async (data: Partial<PodcastProjectCreate>) => {
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
  };

  const updateSegment = async (segmentId: string, data: PodcastSegmentUpdate) => {
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
  };

  const startPipeline = async () => {
    const response = await apiClient.post<{ project_id: string; state: string }>(
      `/podcast/projects/${projectId}/start`,
    );

    // Fetch project to get updated state
    await fetchProject();
    return response.data;
  };

  const pausePipeline = async () => {
    await apiClient.post(`/podcast/projects/${projectId}/pause`);
    await fetchProject();
  };

  const exportAudio = async () => {
    const response = await apiClient.post<Blob>(
      `/podcast/projects/${projectId}/export`,
      {},
      { responseType: 'blob' },
    );

    // Download the file
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `podcast-${projectId}.wav`;
    link.click();
    window.URL.revokeObjectURL(url);

    return response.data;
  };

  useEffect(() => {
    if (projectId) {
      fetchProject();
    }
  }, [projectId]);

  return {
    project,
    loading,
    error,
    refetch: fetchProject,
    updateProject,
    updateSegment,
    startPipeline,
    pausePipeline,
    exportAudio,
  };
}

import type { PodcastSegment } from '@/lib/api/types';
