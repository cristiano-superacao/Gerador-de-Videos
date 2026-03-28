(function () {
    const generationForm = document.getElementById("generation_form");
    const sourceType = document.getElementById("source_type");
    const sourceContent = document.getElementById("source_content");
    const fileGroup = document.getElementById("source_file_group");
    const sourceFile = document.getElementById("source_file");
    const uploadFeedback = document.getElementById("upload_feedback");
    const uploadStatusText = document.getElementById("upload_status_text");
    const uploadPercent = document.getElementById("upload_percent");
    const uploadProgressBar = document.getElementById("upload_progress_bar");
    const generateButton = document.getElementById("generate_button");
    const clientError = document.getElementById("client_error");
    const jobsTableBody = document.getElementById("jobs_table_body");
    const demoBadge = document.getElementById("demo_mode_badge");
    const dashboardConfigElement = document.getElementById("dashboard_config");

    if (!generationForm || !dashboardConfigElement) {
        return;
    }

    const config = JSON.parse(dashboardConfigElement.textContent || "{}");
    const maxUploadBytes = config.maxUploadBytes || 0;
    const allowedExtensions = config.allowedExtensions || [];

    function resetClientError() {
        clientError.textContent = "";
        clientError.classList.add("hidden");
    }

    function showClientError(message) {
        clientError.textContent = message;
        clientError.classList.remove("hidden");
    }

    function resetUploadUi() {
        uploadFeedback.classList.add("hidden");
        uploadStatusText.textContent = config.uploadStatusLabel;
        uploadPercent.textContent = "0%";
        uploadProgressBar.style.width = "0%";
    }

    function toggleInputs() {
        const isVideo = sourceType.value === "video";
        fileGroup.classList.toggle("hidden", !isVideo);
        sourceContent.required = !isVideo;
        sourceFile.required = isVideo;
        resetClientError();
        resetUploadUi();
    }

    function applyJobsPayload(payload) {
        if (!jobsTableBody || !payload || typeof payload.html !== "string") {
            return;
        }

        jobsTableBody.innerHTML = payload.html;

        if (demoBadge) {
            demoBadge.classList.toggle("hidden", !payload.has_demo_mode);
        }
    }

    async function pollJobsStatus() {
        try {
            const response = await fetch(config.pollUrl, {
                method: "GET",
                headers: { Accept: "application/json" },
            });

            if (!response.ok) {
                return;
            }

            const payload = await response.json();
            applyJobsPayload(payload);
        } catch (error) {
            return;
        }
    }

    generationForm.addEventListener("submit", function (event) {
        resetClientError();

        const isVideo = sourceType.value === "video";
        if (!isVideo) {
            return;
        }

        const selectedFile = sourceFile.files && sourceFile.files[0];
        if (!selectedFile) {
            event.preventDefault();
            showClientError(config.missingFileMessage);
            return;
        }

        const extension = selectedFile.name.includes(".")
            ? selectedFile.name.split(".").pop().toLowerCase()
            : "";

        if (!allowedExtensions.includes(extension)) {
            event.preventDefault();
            showClientError(config.invalidExtensionMessage);
            return;
        }

        if (selectedFile.size > maxUploadBytes) {
            event.preventDefault();
            showClientError(config.uploadTooLargeMessage);
            return;
        }

        event.preventDefault();
        uploadFeedback.classList.remove("hidden");
        generateButton.disabled = true;
        generateButton.textContent = config.submitProcessingLabel;

        const xhr = new XMLHttpRequest();
        xhr.open("POST", generationForm.action, true);
        xhr.responseType = "text";

        xhr.upload.onprogress = function (progressEvent) {
            if (!progressEvent.lengthComputable) {
                return;
            }

            const percent = Math.round(
                (progressEvent.loaded / progressEvent.total) * 100
            );
            uploadProgressBar.style.width = `${percent}%`;
            uploadPercent.textContent = `${percent}%`;
            uploadStatusText.textContent = config.uploadStatusLabel;
        };

        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 400) {
                uploadProgressBar.style.width = "100%";
                uploadPercent.textContent = "100%";
                uploadStatusText.textContent = config.finalizingStatusLabel;
                document.open();
                document.write(xhr.responseText);
                document.close();
                return;
            }

            generateButton.disabled = false;
            generateButton.textContent = config.submitDefaultLabel;
            showClientError(config.uploadFailureMessage);
        };

        xhr.onerror = function () {
            generateButton.disabled = false;
            generateButton.textContent = config.submitDefaultLabel;
            showClientError(config.uploadNetworkErrorMessage);
        };

        xhr.send(new FormData(generationForm));
    });

    sourceType.addEventListener("change", toggleInputs);
    toggleInputs();

    pollJobsStatus();
    window.setInterval(pollJobsStatus, config.pollIntervalMs || 8000);
})();