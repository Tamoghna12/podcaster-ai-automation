/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_create_podcast_project_podcast_projects_post } from '../models/Body_create_podcast_project_podcast_projects_post';
import type { Body_update_podcast_project_podcast_projects__project_id__put } from '../models/Body_update_podcast_project_podcast_projects__project_id__put';
import type { Body_update_podcast_segment_podcast_projects__project_id__segments__segment_id__put } from '../models/Body_update_podcast_segment_podcast_projects__project_id__segments__segment_id__put';
import type { HealthResponse } from '../models/HealthResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Root
     * Root endpoint.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rootGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }
    /**
     * Shutdown
     * Gracefully shutdown server.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static shutdownShutdownPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/shutdown',
        });
    }
    /**
     * Health
     * Health check endpoint - Linux + Nvidia GPU compatible.
     * @returns HealthResponse Successful Response
     * @throws ApiError
     */
    public static healthHealthGet(): CancelablePromise<HealthResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/health',
        });
    }
    /**
     * Get Server Mode
     * Get current server mode.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getServerModeServerModeGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/server/mode',
        });
    }
    /**
     * List Podcast Projects
     * List all podcast projects.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listPodcastProjectsPodcastProjectsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/podcast/projects',
        });
    }
    /**
     * Create Podcast Project
     * Create new podcast project from markdown script.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createPodcastProjectPodcastProjectsPost({
        formData,
    }: {
        formData: Body_create_podcast_project_podcast_projects_post,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/podcast/projects',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Podcast Project
     * Get specific podcast project with segments.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPodcastProjectPodcastProjectsProjectIdGet({
        projectId,
    }: {
        projectId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/podcast/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Podcast Project
     * Update podcast project (re-import script).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updatePodcastProjectPodcastProjectsProjectIdPut({
        projectId,
        formData,
    }: {
        projectId: string,
        formData?: Body_update_podcast_project_podcast_projects__project_id__put,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/podcast/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Podcast Project
     * Delete podcast project.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deletePodcastProjectPodcastProjectsProjectIdDelete({
        projectId,
    }: {
        projectId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/podcast/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Podcast Segment
     * Update segment configuration (model size, generation settings).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updatePodcastSegmentPodcastProjectsProjectIdSegmentsSegmentIdPut({
        projectId,
        segmentId,
        formData,
    }: {
        projectId: string,
        segmentId: string,
        formData?: Body_update_podcast_segment_podcast_projects__project_id__segments__segment_id__put,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/podcast/projects/{project_id}/segments/{segment_id}',
            path: {
                'project_id': projectId,
                'segment_id': segmentId,
            },
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Start Podcast Pipeline
     * Start or resume podcast generation pipeline.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static startPodcastPipelinePodcastProjectsProjectIdStartPost({
        projectId,
    }: {
        projectId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/podcast/projects/{project_id}/start',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Pause Podcast Pipeline
     * Pause pipeline (user initiated).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static pausePodcastPipelinePodcastProjectsProjectIdPausePost({
        projectId,
    }: {
        projectId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/podcast/projects/{project_id}/pause',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Podcast Progress
     * Get pipeline progress via SSE.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPodcastProgressPodcastProjectsProjectIdProgressGet({
        projectId,
    }: {
        projectId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/podcast/projects/{project_id}/progress',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export Podcast Audio
     * Export final podcast audio as WAV.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportPodcastAudioPodcastProjectsProjectIdExportPost({
        projectId,
    }: {
        projectId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/podcast/projects/{project_id}/export',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
