import { useEffect, useState, useRef } from "react";

/**
 * Custom React Hook to connect to Server-Sent Events stream for screenplay coverage progress.
 * 
 * @param {string|null} jobId - The job UUID to stream.
 * @returns {{
 *   events: Array<{event: string, agent?: string, message: string}>,
 *   status: 'idle' | 'running' | 'complete' | 'error',
 *   report: any,
 *   error: string | null
 * }}
 */
export function useSSE(jobId) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("idle");
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!jobId) {
      setEvents([]);
      setStatus("idle");
      setReport(null);
      setError(null);
      return;
    }

    setStatus("running");
    setError(null);
    setEvents([]);

    const url = `/api/coverage/${jobId}/stream`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Helper to log and append events
    const addEvent = (evt) => {
      setEvents((prev) => [...prev, evt]);
    };

    // Generic message listener (fallback)
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        addEvent(payload);
      } catch (e) {
        console.error("Failed to parse message event:", e);
      }
    };

    // Agent Start
    eventSource.addEventListener("agent_start", (event) => {
      try {
        const payload = JSON.parse(event.data);
        addEvent(payload);
      } catch (e) {
        console.error("Failed to parse agent_start event:", e);
      }
    });

    // Agent Complete
    eventSource.addEventListener("agent_complete", (event) => {
      try {
        const payload = JSON.parse(event.data);
        addEvent(payload);
      } catch (e) {
        console.error("Failed to parse agent_complete event:", e);
      }
    });

    // Agent Error
    eventSource.addEventListener("agent_error", (event) => {
      try {
        const payload = JSON.parse(event.data);
        addEvent(payload);
      } catch (e) {
        console.error("Failed to parse agent_error event:", e);
      }
    });

    // Global pipeline complete (Final report returned)
    eventSource.addEventListener("complete", (event) => {
      try {
        const payload = JSON.parse(event.data);
        addEvent(payload);
        setStatus("complete");
        setReport(payload.data);
        eventSource.close();
      } catch (e) {
        console.error("Failed to parse complete event:", e);
        setError("Failed to parse complete report data.");
        setStatus("error");
        eventSource.close();
      }
    });

    // Global pipeline error
    eventSource.addEventListener("error", (event) => {
      // Check if it is a network error or explicitly sent error event
      try {
        if (event.data) {
          const payload = JSON.parse(event.data);
          addEvent(payload);
          setError(payload.message || "An error occurred during pipeline execution.");
        } else {
          // EventSource connection error (or completion without explicit close)
          // Often triggered on disconnect. We check if we are already complete.
          setStatus((prev) => {
            if (prev === "complete") return prev;
            setError("Connection to coverage stream lost.");
            return "error";
          });
        }
      } catch (e) {
        setError("Connection to coverage stream closed unexpectedly.");
        setStatus("error");
      }
      eventSource.close();
    });

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [jobId]);

  return { events, status, report, error };
}
