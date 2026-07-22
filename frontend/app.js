document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const jobsList = document.getElementById("jobsList");
    const seedBtn = document.getElementById("seedBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const riskFilter = document.getElementById("riskFilter");
    const uploadProgress = document.getElementById("uploadProgress");
    const progressFill = document.getElementById("progressFill");
    const uploadStatusText = document.getElementById("uploadStatusText");
    const detailModal = document.getElementById("detailModal");
    const closeModalBtn = document.getElementById("closeModalBtn");

    let activeJobs = new Set();
    let pollingInterval = null;

    // Fetch initial analytics summary & jobs list
    fetchAnalytics();
    fetchJobs();

    // Start auto polling every 3 seconds for active jobs
    pollingInterval = setInterval(() => {
        fetchAnalytics();
        fetchJobs();
    }, 3000);

    // Event Listeners
    dropzone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    seedBtn.addEventListener("click", async () => {
        seedBtn.disabled = true;
        seedBtn.innerHTML = "<span>⏳ Seeding...</span>";
        try {
            const res = await fetch("/api/v1/seed", { method: "POST" });
            if (res.ok) {
                fetchJobs();
                fetchAnalytics();
            }
        } catch (err) {
            console.error("Failed to seed demo cases:", err);
        } finally {
            seedBtn.disabled = false;
            seedBtn.innerHTML = "<span>⚡ Seed Demo Cases</span>";
        }
    });

    refreshBtn.addEventListener("click", () => {
        fetchJobs();
        fetchAnalytics();
    });

    riskFilter.addEventListener("change", () => fetchJobs());

    closeModalBtn.addEventListener("click", () => detailModal.classList.add("hidden"));

    // Upload Logic
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append("file", file);

        uploadProgress.classList.remove("hidden");
        progressFill.style.width = "40%";
        uploadStatusText.innerText = `Uploading ${file.name}...`;

        try {
            const res = await fetch("/api/v1/media/upload", {
                method: "POST",
                body: formData
            });

            progressFill.style.width = "100%";
            if (!res.ok) {
                const err = await res.json();
                alert(`Upload failed: ${err.detail || "Error"}`);
                return;
            }

            const data = await res.json();
            uploadStatusText.innerText = "Upload complete! Enqueued for processing.";
            setTimeout(() => uploadProgress.classList.add("hidden"), 2000);

            fetchJobs();
            fetchAnalytics();
        } catch (err) {
            alert(`Upload error: ${err.message}`);
            uploadProgress.classList.add("hidden");
        }
    }

    // Analytics Summary
    async function fetchAnalytics() {
        try {
            const res = await fetch("/api/v1/analytics/summary");
            if (res.ok) {
                const data = await res.json();
                document.getElementById("statTotal").innerText = data.total_jobs;
                document.getElementById("statPass").innerText = data.pass_count;
                document.getElementById("statWarning").innerText = data.warning_count;
                document.getElementById("statReject").innerText = data.reject_count;
                document.getElementById("statLatency").innerText = `${data.avg_processing_time_ms}ms`;
            }
        } catch (err) {
            console.error("Failed to fetch analytics:", err);
        }
    }

    // Fetch Jobs List
    async function fetchJobs() {
        try {
            const filterVal = riskFilter.value;
            const url = filterVal ? `/api/v1/media/list?risk_level=${filterVal}` : `/api/v1/media/list`;
            const res = await fetch(url);
            if (!res.ok) return;

            const data = await res.json();
            if (data.items.length === 0) {
                jobsList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📂</div>
                        <p>No media jobs found.</p>
                        <p class="sub">Click <strong>"Seed Demo Cases"</strong> or upload an image to start processing!</p>
                    </div>`;
                return;
            }

            jobsList.innerHTML = "";
            for (const item of data.items) {
                renderJobCard(item);
            }
        } catch (err) {
            console.error("Failed to fetch jobs:", err);
        }
    }

    function renderJobCard(job) {
        const card = document.createElement("div");
        card.className = "job-card";

        const riskClass = (job.risk_level || job.status).toLowerCase();
        const createdDate = new Date(job.created_at).toLocaleTimeString();

        card.innerHTML = `
            <img src="/uploads/${job.job_id}.jpg" class="job-thumb" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'80\' height=\'60\'><rect width=\'80\' height=\'60\' fill=\'%23222\'/><text x=\'50%\' y=\'50%\' fill=\'%23888\' font-size=\'10\' text-anchor=\'middle\' dy=\'.3em\'>IMAGE</text></svg>'">
            <div class="job-details">
                <div class="job-title-row">
                    <span class="job-filename">${job.filename}</span>
                    <span class="badge ${riskClass}">${job.risk_level || job.status}</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted);">
                    ID: <code>${job.job_id.substring(0, 8)}...</code> • Created at ${createdDate}
                </div>
                <div class="job-issues">
                    ${job.issues_count > 0 ? `<span class="issue-tag">⚠️ ${job.issues_count} Issue(s)</span>` : '<span style="font-size:0.75rem; color:var(--accent-green)">✓ No issues detected</span>'}
                </div>
            </div>
            <div>
                <button class="btn btn-secondary view-details-btn" data-id="${job.job_id}">View Results</button>
            </div>
        `;

        card.querySelector(".view-details-btn").addEventListener("click", () => showJobDetails(job.job_id));
        jobsList.appendChild(card);
    }

    async function showJobDetails(jobId) {
        try {
            const res = await fetch(`/api/v1/media/${jobId}/results`);
            if (!res.ok) {
                const err = await res.json();
                alert(`Cannot view details: ${err.detail}`);
                return;
            }

            const data = await res.json();
            const d = data.details;

            document.getElementById("modalTitle").innerText = `Results: ${data.original_filename}`;
            document.getElementById("modalBody").innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <div>
                        <span class="badge ${data.risk_level.toLowerCase()}" style="font-size:1rem;">Risk: ${data.risk_level}</span>
                        <span style="margin-left:12px; font-weight:700; font-size:1.2rem;">Score: ${data.overall_score} / 100</span>
                    </div>
                    ${d.license_plate_text ? `<div class="plate-badge">🚘 ${d.license_plate_text}</div>` : ''}
                </div>

                <h4 style="margin-bottom:8px;">Detected Issues List</h4>
                ${data.detected_issues.length > 0 
                    ? `<ul style="margin-bottom:16px; padding-left:20px; color:#fca5a5;">${data.detected_issues.map(i => `<li>${i}</li>`).join('')}</ul>`
                    : '<p style="color:var(--accent-green); margin-bottom:16px;">✓ Clean image - All heuristic checks passed</p>'
                }

                <h4 style="margin-bottom:8px;">Detailed Metric Breakdown</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.85rem;">
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:6px;">
                        <strong>Blur Score (Laplacian Var):</strong> ${d.blur_score}<br>
                        <span>Is Blurry: ${d.is_blurry ? '⚠️ YES' : '✓ NO'}</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:6px;">
                        <strong>Brightness Luminance:</strong> ${d.brightness_score}<br>
                        <span>Low Light: ${d.is_low_light ? '⚠️ YES' : '✓ NO'}</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:6px;">
                        <strong>Perceptual Duplicate:</strong> ${d.is_duplicate ? '⚠️ DUPLICATE' : '✓ UNIQUE'}<br>
                        ${d.duplicate_distance !== null ? `<span>Hamming Distance: ${d.duplicate_distance}</span>` : ''}
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:6px;">
                        <strong>Screenshot / Screen Photo:</strong> ${d.is_screenshot ? '⚠️ YES' : '✓ NO'}<br>
                        <span>Score: ${d.screenshot_score} / 100</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:6px;">
                        <strong>Tampering / ELA Disparity:</strong> ${d.is_tampered ? '⚠️ TAMPERED' : '✓ CLEAN'}<br>
                        <span>Tamper Score: ${d.tamper_score} / 100</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:6px;">
                        <strong>License Plate Valid:</strong> ${d.is_valid_license_plate ? '✓ VALID' : '⚠️ INVALID / UNREADABLE'}<br>
                        <span>Confidence: ${d.plate_confidence}%</span>
                    </div>
                </div>
            `;

            detailModal.classList.remove("hidden");
        } catch (err) {
            alert(`Error loading details: ${err.message}`);
        }
    }
});
