class PollUntilValid {
    /**
     *
     * @param url
     * @param fnCondition
     * @param onProgress callback if
     * @param onValid callback
     * @param onError callback
     * @param intervalInMilliseconds
     * @returns {Promise<Response>}
     */
    static async poll(
        url,
        fnCondition,
        onProgress,
        onValid,
        onError,
        intervalInMilliseconds = 1000,
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

        while (fnCondition(response)) {
            await onProgress(response);
            await PollUntilValid.wait(intervalInMilliseconds);
            response = await fetch(url);
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
