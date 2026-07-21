/**
 * API Client for interacting with the Script Doctor Swarm backend.
 */

// Base URL is proxy-handled in Vite dev server (e.g. requests to /api/ are proxied to localhost:8000).
// For standalone or deployed, configure via an environment variable if needed.
const API_BASE = "";

/**
 * Upload a screenplay file to start the coverage pipeline.
 * 
 * @param {File} file - Screenplay file (.txt or .pdf)
 * @returns {Promise<{ job_id: string }>}
 */
export async function uploadScript(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/coverage`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to upload screenplay file.");
  }

  return response.json();
}

/**
 * Retrieve the status and coverage report of a job.
 * 
 * @param {string} jobId - UUID of the job
 * @returns {Promise<{ job_id: string, status: string, report?: any, error?: string }>}
 */
export async function getCoverageReport(jobId) {
  const response = await fetch(`${API_BASE}/api/coverage/${jobId}`);

  if (response.status === 202) {
    // Pipeline is still running
    const data = await response.json();
    return { job_id: jobId, status: data.status };
  }

  if (!response.ok) {
    throw new Error("Failed to fetch coverage report details.");
  }

  return response.json();
}
