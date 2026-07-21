import React, { useState, useRef } from "react";
import { uploadScript } from "../api/client";
import { FileText, Upload, AlertCircle } from "lucide-react";

export default function UploadForm({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const ext = selectedFile.name.split(".").pop().toLowerCase();
    if (ext !== "txt" && ext !== "pdf") {
      setError("Please upload only screenplay files (.txt or .pdf)");
      setFile(null);
      return;
    }
    setError(null);
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const res = await uploadScript(file);
      onUploadSuccess(res.job_id);
    } catch (err) {
      console.error(err);
      setError(err.message || "An error occurred while uploading the screenplay.");
    } finally {
      setLoading(false);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-12 p-4">
      {/* Folder Header Tab Metaphor */}
      <div className="flex">
        <div className="bg-manila text-ink px-6 py-2 rounded-t-lg font-grotesk font-semibold text-sm border-t border-x border-ink relative z-10 select-none">
          NEW SCREENPLAY SUBMISSION
        </div>
        <div className="flex-1 border-b border-ink"></div>
      </div>

      {/* Main Manila Folder Body */}
      <form
        onSubmit={handleSubmit}
        className="bg-manila border border-ink rounded-b-lg rounded-tr-lg p-8 shadow-md relative flex flex-col items-center"
      >
        {/* Subtle physical details (stitches/stamps) */}
        <div className="absolute top-4 right-4 text-xs font-courier opacity-50 uppercase select-none">
          Form 104-B / Reader Copy
        </div>

        {/* Dropzone Area */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileInput}
          className={`w-full h-64 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
            dragActive
              ? "border-red-flag bg-paper/20"
              : "border-ink/40 hover:border-ink hover:bg-paper/10"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.pdf"
            className="hidden"
            onChange={handleChange}
          />

          {file ? (
            <div className="flex flex-col items-center text-ink p-4">
              <FileText size={48} className="text-carbon-blue mb-3" />
              <p className="font-courier font-bold text-center text-sm md:text-base max-w-md break-all">
                {file.name}
              </p>
              <p className="text-xs font-grotesk mt-1 opacity-70">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <p className="text-xs font-grotesk text-red-flag mt-2 underline">
                Click or drag to replace
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center text-ink/75 p-6 text-center select-none">
              <Upload size={40} className="mb-3 opacity-80" />
              <p className="font-grotesk font-medium">
                Drag and drop your screenplay here, or <span className="underline text-red-flag cursor-pointer">browse</span>
              </p>
              <p className="font-courier text-xs mt-3 opacity-60">
                Accepted Formats: Standard Plain Text (.txt) or PDF (.pdf)
              </p>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="w-full mt-4 flex items-center gap-2 p-3 bg-red-flag/10 border border-red-flag text-red-flag rounded font-grotesk text-sm">
            <AlertCircle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Button */}
        <button
          type="submit"
          disabled={!file || loading}
          className={`w-full md:w-auto px-8 py-3 mt-6 border border-ink rounded font-grotesk font-bold transition-all ${
            !file || loading
              ? "opacity-50 cursor-not-allowed bg-paper/50 text-ink/50"
              : "bg-ink text-paper hover:bg-paper hover:text-ink active:translate-y-[1px]"
          }`}
        >
          {loading ? "PARSING SCREENPLAY..." : "RUN MULTI-AGENT COVERAGE"}
        </button>
      </form>
    </div>
  );
}
