/**
 * Thrown by PollUntilValid.poll when no response could be received (fetch rejected),
 * after all network retries are used up. Extends TypeError (what fetch throws) for compatibility.
 */
class NetworkError extends TypeError {
    constructor(cause) {
        super("The request failed due to a network error.", { cause });
        this.name = "NetworkError";
    }
}

class PollUntilValid {
    /**
     * The poll method will repeatedly fetch data from the given URL in the specified amount of
     * interval time.
     * It will do so as long as the validate function does not return "true" or an http code
     * indicates problems.
     * To catch Network errors you should wrap the function call in a try-catch statement.
     * Failed requests (no response) are retried `maxNetworkRetries` times with exponential
     * backoff (interval, 2x interval, 4x interval, ...) before a NetworkError is thrown.
     * The retry counter is reset after every received response.
     *
     * The JSON body of every successful (200-299) response is parsed once by this method and
     * passed as second argument `data` to validateFn, onValid and onProgress.
     * Do not call response.json() in these callbacks, the body has already been consumed.
     *
     * @param {string} url - The URL to poll from
     * @param {function(Response, any): (boolean|Promise<boolean>)} validateFn - Validation
     *     function. Gets the response and the parsed JSON body.
     *     Should return true when the response meets the requirements, so it will stop the polling.
     * @param {int} [intervalInMilliseconds=1000] - The amount of time waiting until
     *     the next request is sent
     * @param {function(Response, any)} [onValid] - opt. callback. Do something with the valid
     *     response and its parsed JSON body.
     * @param {function(Response, any)} [onProgress] - opt. callback to act on "invalid"
     *     e.g. progess responses. Gets the response and its parsed JSON body.
     * @param {function(Response)} [onError] - opt. callback to react on errors
     *     (http status codes other than 200-299). Gets the unread response, as error bodies
     *     are not necessarily JSON.
     * @param {object} [options]
     * @param {int} [options.maxNetworkRetries=0] - How often a failed request is retried
     *     before a NetworkError is thrown.
     * @param {function(int, int, Error)} [options.onNetworkRetry] - opt. callback before each
     *     retry. Gets the retry number (starting at 1), maxNetworkRetries and the fetch error.
     * @returns {Promise<Response>} - The last response (valid or error). Use it to check the
     *     status. Its body has already been consumed for valid responses, use onValid to get the data.
     */
    static async poll(
        url,
        validateFn = () => true,
        intervalInMilliseconds = 1000,
        onValid = () => {},
        onProgress = () => {},
        onError = () => {},
        { maxNetworkRetries = 0, onNetworkRetry = () => {} } = {},
    ) {
        let networkRetries = 0;
        do {
            let response;
            try {
                response = await fetch(url);
            } catch (error) {
                if (networkRetries >= maxNetworkRetries) throw new NetworkError(error);
                networkRetries++;
                await onNetworkRetry(networkRetries, maxNetworkRetries, error);
                await PollUntilValid.wait(intervalInMilliseconds * 2 ** (networkRetries - 1));
                continue;
            }
            networkRetries = 0;

            // if response code is not between 200-299
            if (!response.ok) {
                await onError(response);
                return response;
            }

            const data = await response.json();

            if (!(await validateFn(response, data))) {
                await onProgress(response, data);
                await PollUntilValid.wait(intervalInMilliseconds);
            } else {
                await onValid(response, data);
                return response;
            }

        } while (true);
    }

    static async wait(ms = 1000) {
        return new Promise((resolve) => {
            setTimeout(resolve, ms);
        });
    }
}

export {
    NetworkError,
    PollUntilValid,
};
