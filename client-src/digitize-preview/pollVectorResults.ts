import { Map } from "ol";
import { NetworkError, PollUntilValid } from "../shared";
import {
    createErrorRow,
    showLoadErrorRows,
    showLoadErrorSummary,
    showProcessingError,
    showProcessingErrorsBelowMap,
    showServerErrorDetails
} from "./error-handling";

import { addGeoJSONPreviewLayer } from "./map";

/** JSON body of the /api/status/{uuid}/vector-results endpoint */
interface VectorResultsStatusResponseJson {
    id: string;
    status: ResultStatus;
    type: "vector-results";
    info: { current: number; total: number };
    errors?: string[];
    href?: string;
    msg?: string;
}

const enum ResultStatus {
    Success = "SUCCESS",
    PartialSuccess = "PARTIAL_SUCCESS",
    Failure = "FAILURE",
    Pending = "PENDING"
}

export async function pollVectorResults(url: string, map: Map) {
    setProcessingOverlay(map, true);
    const progressTimer = startProgressTimer();
    try {
        // retries with backoff of 1, 2, 4, 8, 16 s: gives up after ~30 s without connection
        return await PollUntilValid.poll(url, validateFn, 1000, onValid, onProgress, onError, {
            maxNetworkRetries: 5,
            onNetworkRetry,
        });
    } catch (error) {
        console.error(error);
        stopProgressTimer(progressTimer);
        // NetworkError: no response was received at all after all retries
        // (offline, DNS failure, server not reachable, connection reset, request blocked by browser/extension).
        // Other errors are thrown in the callbacks (e.g. invalid JSON body or a bug).
        showProcessingError(error instanceof NetworkError
            ? "Network error.\nPlease check your internet connection."
            : "Unexpected error.\nThis may be a bug.");
    }

    function onNetworkRetry(retry: number, maxRetries: number) {
        const message = `Connection lost, retrying (${retry}/${maxRetries})…`
        showLoadErrorRows([createErrorRow(message)], false);
    }

    function validateFn(response: Response) {
        // valid once the status is 200
        return response.status === 200;
    }

    function onProgress(response: Response, result: VectorResultsStatusResponseJson) {
        // show only a summary (error type + count), the details are listed below the map when finished
        showLoadErrorSummary(result.errors ?? []);
        const { current, total } = result.info;
        updateProgress(current, total, result.status);
    }

    function onValid(response: Response, result: VectorResultsStatusResponseJson) {
        setProcessingOverlay(map, false);
        stopProgressTimer(progressTimer);
        if (result.href) addGeoJSONPreviewLayer(map, result.href);

        // partial success: keep the errors visible below the map after the overlay is gone
        if (result.status === ResultStatus.PartialSuccess) {
            showProcessingErrorsBelowMap(result.errors ?? [], result.msg, false);
        }

    }

    function onError(response: Response, result?: Partial<VectorResultsStatusResponseJson>) {
        if (result?.status) updateProgress(result?.info?.current ?? 0, result?.info?.total ?? 0, result.status);
        // 422 (task failed), 500 or others: only show the HTTP status in a single line in the overlay
        stopProgressTimer(progressTimer);
        // showProcessingError(`${response.status} ${response.statusText}`.trim());

        if (String(response.status).startsWith("4")) {
            // all sketch maps failed
            // remove error messages in map-loading error-box
            showProcessingError();
            // list the errors below the map with a hint to check the uploads
            showProcessingErrorsBelowMap(result?.errors ?? [], result?.msg, true);
        } else /*if (response.status >= 500)*/ {
            showProcessingError();
            // unexpected server error: show details the user can send to the support
            showServerErrorDetails(response);
        }
    }
}

function setProcessingOverlay(map: Map, visible: boolean) {
    // document.querySelector<HTMLElement>("#map-loading")!.hidden = !visible;
    document.querySelector<HTMLElement>("#map-loading")!.classList.toggle("is-hidden", !visible);
    const target = map.getTargetElement()!;
    target.inert = visible;
    // target.setAttribute("aria-busy", String(visible));
}

function updateProgress(parts: number, total: number, message?: string) {
    const progressPercent = (parts / total) * 100;
    document.querySelector<HTMLElement>("#load-parts")!.textContent = `${parts}/${total}`;
    // start with infinite progress bar (without value), after first result switch to percent
    if (typeof progressPercent === "number" && progressPercent > 0) {
        document.querySelector<HTMLProgressElement>("#load-progress")!.value = progressPercent;
        document.querySelector<HTMLElement>("#load-percent")!.textContent = `${Math.round(progressPercent)} %`;
    }
    if (message) document.querySelector<HTMLElement>("#load-message")!.textContent = message;
}

function startProgressTimer() {
    const start = Date.now();
    return setInterval(() => {
        const s = Math.floor((Date.now() - start) / 1000);
        document.querySelector<HTMLElement>("#load-elapsed")!.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    }, 1000);
}

function stopProgressTimer(timerReference: ReturnType<typeof setInterval>) {
    clearInterval(timerReference);
}
