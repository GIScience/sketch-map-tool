import { PollUntilValid } from "./pollUntilValid.js";
import {
    setDownloadLink,
    setIsBusy,
    setDisabled,
    setTaskStatus,
} from "../domHelpers.js";

/**
 * This function polls repeatedly data from a URL as long as it receives
 *     HTTP 202 Accepted Codes.
 *     It will stop if it gets a 200 OK or any Code outside the range of 200-299.
 *     Depending on Success(200), Pending(202), or any failure (!200-299) it
 *     will display different messages to the user.
 *     On NetworkError it will continue polling.
 *
 *     The function assumes the availability of 2 HTML Elements with the following ids:
 *     @example
 *     <span id="YOUR_PREFIX_HERE-status"></span>
 *     <a id="YOUR_PREFIX_HERE-download-button"></a>
 *
 * @param url url to poll from
 * @param prefix identifier used to decide where results or progress messages should be displayed
 * @returns {Promise<Response>}
 */
async function poll(url, prefix) {
    function validateFn(response) {
        // valid once the status is 200
        return response.status === 200;
    }

    async function onProgress(response) {
        // console.log("progress", response);
        const result = await response.json();
        setTaskStatus(`${prefix}-status`, `Processing ${result.status}`);
    }

    async function onValid(response) {
        const result = await response.json();
        const { href } = result;
        setTaskStatus(`${prefix}-status`, "");
        setDownloadLink(`${prefix}-download-button`, href);
        setIsBusy(`${prefix}-download-button`, false);
        setDisabled(`${prefix}-download-button`, false);

        // hide all .pending elements and show all .success elements
        document.querySelectorAll(`#${prefix} .pending`).forEach((element) => element.classList.toggle("hidden"));
        document.querySelectorAll(`#${prefix} .success`).forEach((element) => element.classList.toggle("hidden"));
    }

    /**
     * Displays an error message and disappears the download button
     * @param _prefix sketch-map | quality-report
     * @param errorText text shown in the error message details
     */
    function handleError(_prefix, errorText) {
        document.querySelectorAll(`#${prefix} :is(.pending, .success)`)
            .forEach((element) => element.classList.add("hidden"));
        document.querySelectorAll(`#${prefix} .error`)
            .forEach((element) => {
                element.classList.remove("hidden");
                const errorElementString = `<p><details><summary>Error Details</summary>${errorText}</details></p>`;
                const errorElement = document.createRange()
                    .createContextualFragment(errorElementString);
                element.appendChild(errorElement);
            });

        // a button to disappear
        document.getElementById(`${_prefix}-download-button`).style.display = "none";
    }

    async function onError(response) {
        const { status: httpStatus } = response;
        const resonseJSON = await response.json();
        const {
            error: errorText,
            status: taskStatus,
        } = resonseJSON;
        // display error
        if (httpStatus === 500) {
            handleError(prefix, `${new Date().toISOString()} ${taskStatus} <br>
            There was an Internal Server Error.`);
        } else {
            handleError(prefix, `${new Date().toISOString()} ${taskStatus} <br> ${errorText}`);
        }
        // remove task status
        setTaskStatus(`${prefix}-status`, "");
    }

    try {
        return await PollUntilValid.poll(url, validateFn, 1000, onValid, onProgress, onError);
    } catch (error) {
        if (error instanceof TypeError) {
            // Chrome and Firefox use different Error messages, so it's hard to be more
            // specific than checking for TypeError
            // see: https://developer.mozilla.org/en-US/docs/Web/API/fetch#exceptions
            setTaskStatus(`${prefix}-status`, "NetworkError: RETRYING to get task status");
            await PollUntilValid.wait(5000);
            return poll(url, prefix);
        }
        throw error;
    }
}

export {
    poll,
};
