import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { JobDetail, JobDetectionsResponse, DetectionItem } from '../types';
import { ApiClient } from '../api/client';
import { Card } from '../components/common/Card';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

const ALLOWED_EXTS = ['.mp4', '.avi', '.mov', '.mkv'];
const MAX_SIZE_MB = 500;

export const VideoAnalysisView: React.FC = () => {
  // Upload form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [zoneId, setZoneId] = useState<string>('ZONE-01');
  const [samplingInterval, setSamplingInterval] = useState<number>(2.0);
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.5);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  // Job queue state
  const [jobs, setJobs] = useState<JobDetail[]>([]);
  const [loadingJobs, setLoadingJobs] = useState<boolean>(true);
  const [jobsError, setJobsError] = useState<string | null>(null);

  // Selected job & detection inspector state
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [detectionsData, setDetectionsData] = useState<JobDetectionsResponse | null>(null);
  const [selectedFrame, setSelectedFrame] = useState<DetectionItem | null>(null);
  const [loadingDetections, setLoadingDetections] = useState<boolean>(false);
  const [detectionsError, setDetectionsError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const isMountedRef = useRef<boolean>(true);

  // Fetch jobs list
  const fetchJobs = useCallback(async () => {
    try {
      const data = await ApiClient.getJobs();
      if (isMountedRef.current) {
        setJobs(data.jobs);
        setJobsError(null);

        // Auto-select latest completed or active job if none selected
        if (!selectedJobId && data.jobs.length > 0) {
          const firstCompleted = data.jobs.find(j => j.status === 'completed') || data.jobs[0];
          setSelectedJobId(firstCompleted.id);
        }
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setJobsError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoadingJobs(false);
      }
    }
  }, [selectedJobId]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchJobs();
    return () => {
      isMountedRef.current = false;
    };
  }, [fetchJobs]);

  // Polling loop for active jobs (status === 'queued' || status === 'processing')
  useEffect(() => {
    const hasActiveJobs = jobs.some(j => j.status === 'queued' || j.status === 'processing');
    if (!hasActiveJobs) return;

    const interval = setInterval(async () => {
      try {
        const data = await ApiClient.getJobs();
        if (isMountedRef.current) {
          setJobs(data.jobs);
          // If selected job just completed, refresh its detections
          if (selectedJobId) {
            const currentSelected = data.jobs.find(j => j.id === selectedJobId);
            if (currentSelected?.status === 'completed' && !detectionsData) {
              loadDetectionsForJob(selectedJobId);
            }
          }
        }
      } catch {
        // Tolerated polling hiccup
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobs, selectedJobId, detectionsData]);

  // Load detections when selectedJobId changes
  const loadDetectionsForJob = useCallback(async (jobId: string) => {
    setLoadingDetections(true);
    setDetectionsError(null);
    try {
      const data = await ApiClient.getJobDetections(jobId);
      if (isMountedRef.current) {
        setDetectionsData(data);
        if (data.detections.length > 0) {
          setSelectedFrame(data.detections[0]);
        } else {
          setSelectedFrame(null);
        }
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setDetectionsError(err instanceof Error ? err.message : String(err));
        setDetectionsData(null);
        setSelectedFrame(null);
      }
    } finally {
      if (isMountedRef.current) {
        setLoadingDetections(false);
      }
    }
  }, []);

  useEffect(() => {
    if (selectedJobId) {
      const targetJob = jobs.find(j => j.id === selectedJobId);
      if (targetJob && targetJob.status === 'completed') {
        loadDetectionsForJob(selectedJobId);
      } else {
        setDetectionsData(null);
        setSelectedFrame(null);
      }
    }
  }, [selectedJobId, jobs, loadDetectionsForJob]);

  // File selection & validation
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    setUploadSuccess(null);
    if (!e.target.files || e.target.files.length === 0) {
      setSelectedFile(null);
      return;
    }

    const file = e.target.files[0];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!ALLOWED_EXTS.includes(ext)) {
      setUploadError(`Invalid file format '${ext}'. Allowed video extensions: ${ALLOWED_EXTS.join(', ')}`);
      setSelectedFile(null);
      return;
    }

    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > MAX_SIZE_MB) {
      setUploadError(`File size (${sizeMb.toFixed(1)} MB) exceeds the maximum allowed limit of ${MAX_SIZE_MB} MB.`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  // Submit upload
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a valid video file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('zone_id', zoneId);
    formData.append('sampling_interval_sec', samplingInterval.toString());
    formData.append('confidence_threshold', confidenceThreshold.toString());

    try {
      const result = await ApiClient.uploadVideo(formData, (percent) => {
        setUploadProgress(percent);
      });

      setUploadSuccess(`Video '${result.original_filename}' uploaded successfully. Job queued for VisionX inference.`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchJobs();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  // Retry failed job
  const handleRetryJob = async (job: JobDetail) => {
    try {
      const newJob = await ApiClient.createJob({
        video_id: job.video_id,
        zone_id: job.zone_id || 'ZONE-01',
        sampling_interval_sec: job.sampling_interval_sec,
        confidence_threshold: job.confidence_threshold,
      });
      setSelectedJobId(newJob.id);
      fetchJobs();
    } catch (err: unknown) {
      alert(`Failed to restart job: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const activeJob = jobs.find(j => j.id === selectedJobId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{
        padding: 'var(--space-4) var(--space-5)',
        backgroundColor: 'var(--color-carbon-lift)',
        border: 'var(--border-hairline)',
        borderRadius: 'var(--radius-xs)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
            MODULE A // VISIONX INFERENCE & CROWD TELEMETRY
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 500, letterSpacing: '-0.02em', marginTop: '2px' }}>
            OpenCV Video Sampling & YOLOv8 Person Detection
          </h1>
        </div>
        <button
          onClick={fetchJobs}
          disabled={loadingJobs}
          className="btn btn-secondary"
        >
          {loadingJobs ? 'SYNCING...' : 'REFRESH JOBS'}
        </button>
      </div>

      {/* Grid: Upload Form + Jobs Queue */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 420px) 1fr', gap: 'var(--space-6)' }}>
        {/* Section 1: Video Upload Form */}
        <Card
          title="Ingest Video Stream"
          subtitle="FILE VALIDATION & INFERENCE PARAMETERS"
          badge={<StatusBadge status="active" label="YOLOV8 READY" />}
        >
          <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {/* File Drop Area */}
            <div style={{
              border: selectedFile ? '1px solid var(--color-metric-green)' : '1px dashed var(--color-ash-stroke)',
              backgroundColor: 'var(--color-obsidian-canvas)',
              padding: 'var(--space-5)',
              borderRadius: 'var(--radius-xs)',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}>
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.avi,.mov,.mkv"
                onChange={handleFileChange}
                disabled={isUploading}
                style={{ display: 'none' }}
                id="video-file-input"
              />
              <label
                htmlFor="video-file-input"
                style={{ cursor: isUploading ? 'not-allowed' : 'pointer', color: 'var(--color-bone)' }}
              >
                <div style={{ fontSize: '13px', fontWeight: 500 }}>
                  {selectedFile ? selectedFile.name : 'Click to select CCTV footage or test video'}
                </div>
                <div className="mono-caption" style={{ marginTop: '4px' }}>
                  {selectedFile
                    ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • READY FOR DISPATCH`
                    : 'MP4, AVI, MOV, MKV • MAXIMUM 500 MB'}
                </div>
              </label>
            </div>

            {/* Zone Selector */}
            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                MONITORED VENUE ZONE
              </label>
              <select
                value={zoneId}
                onChange={(e) => setZoneId(e.target.value)}
                disabled={isUploading}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  backgroundColor: 'var(--color-obsidian-canvas)',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-bone)',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '13px',
                }}
              >
                <option value="ZONE-01">Zone 01 — Main Entrance & Concourse</option>
                <option value="ZONE-02">Zone 02 — Central Gathering Plaza</option>
                <option value="ZONE-03">Zone 03 — North Food Court & Corridor</option>
                <option value="ZONE-04">Zone 04 — East Arcade Pavilion</option>
                <option value="ZONE-05">Zone 05 — West Promenade</option>
              </select>
            </div>

            {/* Sampling Rate & Threshold */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
              <div>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  SAMPLING INTERVAL (SEC)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="30"
                  value={samplingInterval}
                  onChange={(e) => setSamplingInterval(parseFloat(e.target.value) || 2.0)}
                  disabled={isUploading}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: 'var(--border-hairline)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--color-bone)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                  }}
                />
              </div>

              <div>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  CONFIDENCE CUTOFF
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0.1"
                  max="1.0"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value) || 0.5)}
                  disabled={isUploading}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: 'var(--border-hairline)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--color-bone)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                  }}
                />
              </div>
            </div>

            {/* Upload Progress Bar */}
            {isUploading && uploadProgress !== null && (
              <div style={{ marginTop: 'var(--space-2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span className="mono-caption">TRANSMITTING VIDEO STREAM</span>
                  <span className="mono-metric">{uploadProgress}%</span>
                </div>
                <div style={{ height: '4px', backgroundColor: '#262220', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${uploadProgress}%`,
                    height: '100%',
                    backgroundColor: 'var(--color-signal-orange)',
                    transition: 'width 0.15s ease',
                  }} />
                </div>
              </div>
            )}

            {/* Feedback Alerts */}
            {uploadError && (
              <div style={{
                backgroundColor: '#2b1414',
                border: '1px solid var(--color-alert-red)',
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-xs)',
                fontSize: '12px',
                color: 'var(--color-bone)',
              }}>
                <div className="mono-caption" style={{ color: 'var(--color-alert-red)', marginBottom: '2px' }}>
                  UPLOAD REJECTED
                </div>
                {uploadError}
              </div>
            )}

            {uploadSuccess && (
              <div style={{
                backgroundColor: '#162b14',
                border: '1px solid var(--color-metric-green)',
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-xs)',
                fontSize: '12px',
                color: 'var(--color-bone)',
              }}>
                <div className="mono-caption" style={{ color: 'var(--color-metric-green)', marginBottom: '2px' }}>
                  INFERENCE QUEUED
                </div>
                {uploadSuccess}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 'var(--space-2)' }}
            >
              {isUploading ? 'INGESTING VIDEO...' : 'DISPATCH TO VISIONX PIPELINE'}
            </button>
          </form>
        </Card>

        {/* Section 2: Processing Jobs Queue & History */}
        <Card
          title="Inference Queue & Execution History"
          subtitle="OPENCV EXTRACTION & YOLOV8 WORKER STATUS"
          badge={<StatusBadge status="active" label={`${jobs.length} JOBS RECORDED`} />}
        >
          {loadingJobs && jobs.length === 0 && (
            <LoadingSpinner message="POLLING VISIONX JOBS..." />
          )}

          {jobsError && (
            <div style={{
              backgroundColor: '#2b1414',
              border: '1px solid var(--color-alert-red)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '12px',
              color: 'var(--color-bone)',
              marginBottom: 'var(--space-4)',
            }}>
              Error fetching jobs: {jobsError}
            </div>
          )}

          {!loadingJobs && jobs.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: 'var(--space-8)',
              color: 'var(--color-warm-granite)',
              backgroundColor: 'var(--color-obsidian-canvas)',
              border: '1px dashed var(--color-ash-stroke)',
              borderRadius: 'var(--radius-xs)',
            }}>
              <div className="mono-caption" style={{ marginBottom: 'var(--space-2)' }}>
                NO PROCESSING JOBS RECORDED
              </div>
              <div style={{ fontSize: '13px' }}>
                Upload video footage above to trigger real OpenCV extraction and YOLO person detection.
              </div>
            </div>
          )}

          {jobs.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Select</th>
                    <th>Source Video</th>
                    <th>Zone</th>
                    <th>Status</th>
                    <th>Progress / Frames</th>
                    <th>Detections</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => {
                    const isSelected = job.id === selectedJobId;
                    return (
                      <tr
                        key={job.id}
                        onClick={() => setSelectedJobId(job.id)}
                        style={{
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'rgba(238, 96, 24, 0.08)' : undefined,
                        }}
                      >
                        <td>
                          <input
                            type="radio"
                            name="selected-job"
                            checked={isSelected}
                            onChange={() => setSelectedJobId(job.id)}
                            style={{ cursor: 'pointer', accentColor: 'var(--color-signal-orange)' }}
                          />
                        </td>
                        <td style={{ fontWeight: 500 }}>
                          <div>{job.original_filename}</div>
                          <div className="mono-caption" style={{ fontSize: '10px' }}>
                            {(job.file_size_bytes / (1024 * 1024)).toFixed(1)} MB • {job.sampling_interval_sec}s step • conf ≥ {job.confidence_threshold}
                          </div>
                        </td>
                        <td>
                          <span className="mono-caption" style={{
                            padding: '1px 6px',
                            backgroundColor: '#161413',
                            border: '1px solid var(--color-ash-stroke)',
                            borderRadius: 'var(--radius-xs)',
                          }}>
                            {job.zone_id || 'ZONE-01'}
                          </span>
                        </td>
                        <td>
                          <StatusBadge
                            status={
                              job.status === 'completed'
                                ? 'healthy'
                                : job.status === 'processing'
                                ? 'active'
                                : job.status === 'queued'
                                ? 'pending'
                                : 'offline'
                            }
                            label={job.status.toUpperCase()}
                          />
                        </td>
                        <td style={{ minWidth: '130px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                              <span className="mono-metric">{job.progress_percent.toFixed(0)}%</span>
                              {job.total_frames_to_process > 0 && (
                                <span className="mono-caption" style={{ fontSize: '10px' }}>
                                  {job.current_frame}/{job.total_frames_to_process} F
                                </span>
                              )}
                            </div>
                            <div style={{
                              height: '4px',
                              backgroundColor: '#262220',
                              borderRadius: '2px',
                              overflow: 'hidden',
                            }}>
                              <div style={{
                                width: `${job.progress_percent}%`,
                                height: '100%',
                                backgroundColor:
                                  job.status === 'completed'
                                    ? 'var(--color-metric-green)'
                                    : job.status === 'failed'
                                    ? 'var(--color-alert-red)'
                                    : 'var(--color-signal-orange)',
                                transition: 'width 0.3s ease',
                              }} />
                            </div>
                            {job.error_message && (
                              <span style={{ fontSize: '10px', color: 'var(--color-alert-red)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '160px' }}>
                                {job.error_message}
                              </span>
                            )}
                          </div>
                        </td>
                        <td>
                          {job.status === 'completed' ? (
                            <div>
                              <span className="mono-metric" style={{ color: 'var(--color-signal-orange)', fontWeight: 600 }}>
                                {job.max_person_count} max
                              </span>
                              <div className="mono-caption" style={{ fontSize: '10px' }}>
                                {job.total_persons_detected} total
                              </div>
                            </div>
                          ) : (
                            <span className="mono-caption" style={{ color: 'var(--color-warm-granite)' }}>—</span>
                          )}
                        </td>
                        <td>
                          {job.status === 'failed' ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRetryJob(job);
                              }}
                              className="btn btn-secondary"
                              style={{ padding: '2px 8px', fontSize: '10px' }}
                            >
                              RETRY
                            </button>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedJobId(job.id);
                              }}
                              className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ padding: '2px 8px', fontSize: '10px' }}
                            >
                              {isSelected ? 'ACTIVE' : 'INSPECT'}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {/* Section 3: Detection Results & Evidence Frame Inspector */}
      {selectedJobId && (
        <Card
          title={`VisionX Detection Telemetry // Job ${selectedJobId.slice(0, 8)}...`}
          subtitle="AUTHENTICATED EVIDENCE FRAMES & BOUNDING BOX ANALYSIS"
          badge={
            activeJob ? (
              <StatusBadge
                status={activeJob.status === 'completed' ? 'healthy' : activeJob.status === 'processing' ? 'active' : 'offline'}
                label={activeJob.status.toUpperCase()}
              />
            ) : undefined
          }
        >
          {/* Boundary and AI Ethics Notice */}
          <div style={{
            backgroundColor: 'rgba(238, 96, 24, 0.06)',
            border: '1px solid rgba(238, 96, 24, 0.25)',
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-xs)',
            marginBottom: 'var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
          }}>
            <span style={{ color: 'var(--color-signal-orange)', fontSize: '16px' }}>ℹ</span>
            <div style={{ fontSize: '12px', color: 'var(--color-bone)' }}>
              <strong>Detection Methodology & Integrity:</strong> Model detections identify general person bounding boxes (COCO Class 0) per sampled frame. NEXORA does not perform facial recognition, identity re-identification, or behavioral speculation. Repeated frame detections represent localized counts, not unique individual identities.
            </div>
          </div>

          {/* Job In-Progress Banner */}
          {activeJob && activeJob.status === 'processing' && (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center' }}>
              <LoadingSpinner message={`PROCESSING VIDEO STREAM (${activeJob.progress_percent.toFixed(0)}% COMPLETE)...`} />
              <div className="mono-caption" style={{ marginTop: 'var(--space-3)' }}>
                OpenCV is sampling frames every {activeJob.sampling_interval_sec}s and executing YOLOv8n inference.
              </div>
            </div>
          )}

          {/* Job Failed Banner */}
          {activeJob && activeJob.status === 'failed' && (
            <div style={{
              padding: 'var(--space-5)',
              backgroundColor: '#2b1414',
              border: '1px solid var(--color-alert-red)',
              borderRadius: 'var(--radius-xs)',
              textAlign: 'center',
            }}>
              <div className="mono-caption" style={{ color: 'var(--color-alert-red)', marginBottom: 'var(--space-2)' }}>
                INFERENCE PIPELINE TERMINATED WITH ERROR
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-bone)', marginBottom: 'var(--space-4)' }}>
                {activeJob.error_message || 'Video stream could not be decoded or processed.'}
              </div>
              <button
                onClick={() => handleRetryJob(activeJob)}
                className="btn btn-primary"
              >
                RETRY VIDEO ANALYSIS
              </button>
            </div>
          )}

          {/* Job Completed: Show Detections */}
          {activeJob && activeJob.status === 'completed' && (
            <div>
              {loadingDetections && <LoadingSpinner message="FETCHING FRAME DETECTIONS & EVIDENCE..." />}

              {detectionsError && (
                <div style={{
                  padding: 'var(--space-4)',
                  backgroundColor: '#2b1414',
                  border: '1px solid var(--color-alert-red)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-bone)',
                  fontSize: '12px',
                }}>
                  Failed to load detections: {detectionsError}
                </div>
              )}

              {detectionsData && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
                  {/* Summary Metric Strip */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: 'var(--space-4)',
                    padding: 'var(--space-4)',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: 'var(--border-hairline)',
                    borderRadius: 'var(--radius-xs)',
                  }}>
                    <div>
                      <div className="mono-caption">SAMPLED FRAMES</div>
                      <div className="mono-metric" style={{ fontSize: '20px', marginTop: '2px' }}>
                        {detectionsData.total_frames_processed}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', color: 'var(--color-warm-granite)' }}>
                        {activeJob.sampling_interval_sec}s SAMPLING STEP
                      </div>
                    </div>
                    <div>
                      <div className="mono-caption">PEAK PERSON COUNT</div>
                      <div className="mono-metric" style={{ fontSize: '20px', marginTop: '2px', color: 'var(--color-signal-orange)' }}>
                        {detectionsData.max_person_count}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', color: 'var(--color-warm-granite)' }}>
                        MAX DETECTED IN A FRAME
                      </div>
                    </div>
                    <div>
                      <div className="mono-caption">CUMULATIVE DETECTIONS</div>
                      <div className="mono-metric" style={{ fontSize: '20px', marginTop: '2px' }}>
                        {detectionsData.total_persons_detected}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', color: 'var(--color-warm-granite)' }}>
                        ACROSS ALL SAMPLED FRAMES
                      </div>
                    </div>
                    <div>
                      <div className="mono-caption">DETECTION MODEL</div>
                      <div className="mono-metric" style={{ fontSize: '20px', marginTop: '2px', color: 'var(--color-metric-green)' }}>
                        {activeJob.model_name.toUpperCase()}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', color: 'var(--color-warm-granite)' }}>
                        CONFIDENCE ≥ {activeJob.confidence_threshold}
                      </div>
                    </div>
                  </div>

                  {/* Frame Scrubber Timeline & Evidence Inspector */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 340px) 1fr', gap: 'var(--space-5)' }}>
                    {/* Left: Sampled Frames Timeline List */}
                    <div style={{
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: 'var(--border-hairline)',
                      borderRadius: 'var(--radius-xs)',
                      padding: 'var(--space-3)',
                      maxHeight: '520px',
                      overflowY: 'auto',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)',
                    }}>
                      <div className="mono-caption" style={{ padding: 'var(--space-2) var(--space-2)' }}>
                        SAMPLED FRAME TIMELINE ({detectionsData.detections.length} EXTRACTED)
                      </div>

                      {detectionsData.detections.length === 0 ? (
                        <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--color-warm-granite)', fontSize: '12px' }}>
                          No sampled frames recorded.
                        </div>
                      ) : (
                        detectionsData.detections.map((d, idx) => {
                          const isFrameActive = selectedFrame?.id === d.id;
                          return (
                            <div
                              key={d.id}
                              onClick={() => setSelectedFrame(d)}
                              style={{
                                padding: 'var(--space-3)',
                                backgroundColor: isFrameActive ? 'var(--color-carbon-lift)' : '#161413',
                                border: isFrameActive ? '1px solid var(--color-signal-orange)' : '1px solid var(--color-ash-stroke)',
                                borderRadius: 'var(--radius-xs)',
                                cursor: 'pointer',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                transition: 'all 0.15s ease',
                              }}
                            >
                              <div>
                                <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-bone)' }}>
                                  Frame #{idx + 1} • {d.timestamp_seconds.toFixed(1)}s
                                </div>
                                <div className="mono-caption" style={{ fontSize: '10px', color: 'var(--color-warm-granite)', marginTop: '2px' }}>
                                  Raw Index: {d.frame_index} • Conf: {(d.avg_confidence * 100).toFixed(0)}%
                                </div>
                              </div>
                              <span style={{
                                padding: '2px 8px',
                                borderRadius: 'var(--radius-xs)',
                                fontSize: '12px',
                                fontFamily: 'var(--font-mono)',
                                fontWeight: 600,
                                backgroundColor: d.person_count > 0 ? 'rgba(238, 96, 24, 0.15)' : '#262220',
                                color: d.person_count > 0 ? 'var(--color-signal-orange)' : 'var(--color-warm-granite)',
                                border: d.person_count > 0 ? '1px solid rgba(238, 96, 24, 0.4)' : '1px solid var(--color-ash-stroke)',
                              }}>
                                {d.person_count} {d.person_count === 1 ? 'PERSON' : 'PERSONS'}
                              </span>
                            </div>
                          );
                        })
                      )}
                    </div>

                    {/* Right: Selected Evidence Frame & Bounding Box Telemetry */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-4)',
                    }}>
                      {selectedFrame ? (
                        <>
                          {/* Evidence Frame Image */}
                          <div style={{
                            backgroundColor: 'var(--color-obsidian-canvas)',
                            border: 'var(--border-hairline)',
                            borderRadius: 'var(--radius-xs)',
                            overflow: 'hidden',
                            position: 'relative',
                          }}>
                            {selectedFrame.evidence_image_url ? (
                              <img
                                src={ApiClient.getEvidenceImageUrl(selectedFrame.evidence_image_url)}
                                alt={`Evidence frame at ${selectedFrame.timestamp_seconds}s`}
                                style={{
                                  width: '100%',
                                  height: 'auto',
                                  maxHeight: '380px',
                                  objectFit: 'contain',
                                  display: 'block',
                                  backgroundColor: '#000',
                                }}
                              />
                            ) : (
                              <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-warm-granite)' }}>
                                No evidence image available for this frame.
                              </div>
                            )}

                            {/* Overlay Badge */}
                            <div style={{
                              position: 'absolute',
                              bottom: '10px',
                              right: '10px',
                              backgroundColor: 'rgba(16, 16, 16, 0.85)',
                              border: '1px solid var(--color-ash-stroke)',
                              borderRadius: 'var(--radius-xs)',
                              padding: '4px 8px',
                              fontSize: '11px',
                              fontFamily: 'var(--font-mono)',
                              color: 'var(--color-bone)',
                            }}>
                              TIMESTAMP: {selectedFrame.timestamp_seconds.toFixed(2)}s | COUNT: {selectedFrame.person_count}
                            </div>
                          </div>

                          {/* Bounding Box Detail Inspector */}
                          <div style={{
                            backgroundColor: 'var(--color-obsidian-canvas)',
                            border: 'var(--border-hairline)',
                            borderRadius: 'var(--radius-xs)',
                            padding: 'var(--space-4)',
                          }}>
                            <div className="mono-caption" style={{ marginBottom: 'var(--space-3)' }}>
                              BOUNDING BOX COORDINATES & CONFIDENCE SCORES ({selectedFrame.bounding_boxes.length} DETECTED)
                            </div>

                            {selectedFrame.bounding_boxes.length === 0 ? (
                              <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)' }}>
                                No persons detected in this frame above the confidence threshold ({activeJob.confidence_threshold}).
                              </div>
                            ) : (
                              <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
                                <table className="data-table">
                                  <thead>
                                    <tr>
                                      <th>#</th>
                                      <th>Class</th>
                                      <th>Confidence</th>
                                      <th>Bounding Box (X1, Y1, X2, Y2)</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {selectedFrame.bounding_boxes.map((box, bIdx) => (
                                      <tr key={bIdx}>
                                        <td className="mono-metric" style={{ fontSize: '11px' }}>{bIdx + 1}</td>
                                        <td>
                                          <span className="mono-caption" style={{
                                            padding: '1px 6px',
                                            backgroundColor: '#161413',
                                            border: '1px solid var(--color-ash-stroke)',
                                            borderRadius: 'var(--radius-xs)',
                                            color: 'var(--color-signal-orange)',
                                          }}>
                                            {box.class_name.toUpperCase()}
                                          </span>
                                        </td>
                                        <td className="mono-metric" style={{ fontSize: '12px', color: 'var(--color-metric-green)' }}>
                                          {(box.confidence * 100).toFixed(1)}%
                                        </td>
                                        <td className="mono-metric" style={{ fontSize: '11px' }}>
                                          [{box.x1.toFixed(0)}, {box.y1.toFixed(0)}, {box.x2.toFixed(0)}, {box.y2.toFixed(0)}]
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        </>
                      ) : (
                        <div style={{
                          padding: 'var(--space-8)',
                          backgroundColor: 'var(--color-obsidian-canvas)',
                          border: '1px dashed var(--color-ash-stroke)',
                          borderRadius: 'var(--radius-xs)',
                          textAlign: 'center',
                          color: 'var(--color-warm-granite)',
                        }}>
                          Select a sampled frame from the timeline on the left to inspect evidence.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
