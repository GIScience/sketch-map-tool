class PollUntilValid {
    /**
     * The poll method will repeatedly fetch data from the given URL in the specified amount of
     * interval time.
     * It will do so as long as the validate function does not return "true" or an http code
     * indicates problems.
     * To catch Network errors you should wrap the function call in a try-catch statement.
     *
     * @param {string} url - The URL to poll from
     * @param {function(Response)} validateFn - Validation function. Gets the response as param.
     *     Should return true when the response meets the requirements, so it will stop the polling.
     * @param {int} [intervalInMilliseconds=1000] - The amount of time waiting until
     *     the next request is sent
     * @param {function(Response)} [onValid] - opt. callback. Do something with the valid response.
     * @param {function(Response)} [onProgress] - opt. callback to act on "invalid"
     *     e.g. progess responses
     * @param {function(Response)} [onError] - opt. callback to react on errors
     *     (http status codes other than 200-299)
     * @returns {Promise<Response>} - The last "valid" response. Use this or the onValid callback.
     */
    static async poll(
        url,
        validateFn = () => true,
        intervalInMilliseconds = 1000,
        onValid = () => {},
        onProgress = () => {},
        onError = () => {},
    ) {
        let response = await fetch(url);

        // if response code is not between 200-299
        if (!response.ok) {
            if (onError instanceof Function) {
                await onError(response);
                return response;
            }
            throw new Error(`The server responded with an Error: ${response.status} ${response.statusText}`);
        }

        while (!validateFn(response)) {
            /* eslint-disable no-await-in-loop */
            await onProgress(response);
            await PollUntilValid.wait(intervalInMilliseconds);
            response = await fetch(url);
            /* eslint-enable */
        }
        await onValid(response);
        return response;
    }

    static async wait(ms = 1000) {
        return new Promise((resolve) => {
            setTimeout(resolve, ms);
        });
    }
}

export {
    PollUntilValid,
};
