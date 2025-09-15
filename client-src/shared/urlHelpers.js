// TODO: move UUID URL thingy from DOM helper to here

const setAllQueryParam = (params) => {
    const url = new URL(window.location);
    Object.keys(params).forEach((key) => {
        url.searchParams.set(key, params[key]);
    });
    window.history.replaceState({}, "", url);
};

const updateQueryParam = (paramName, newValue) => {
    const url = new URL(window.location);
    url.searchParams.set(paramName, newValue);
    window.history.replaceState({}, "", url);
};

let lastChangeTime = 0;
let debounceTimeout = null;

const updateQueryParamWithConditionalDebounce = (paramName, value) => {
    const now = Date.now();
    const timeSinceLastChange = now - lastChangeTime;

    if (timeSinceLastChange < 300) {
    // If last change was recent, debounce
    // to avoid making too many calls to Location or History APIs within a short timeframe
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            updateQueryParam(paramName, value);
            lastChangeTime = Date.now();
        }, 300);
    } else {
    // Otherwise, update immediately
        updateQueryParam(paramName, value);
        lastChangeTime = now;
    }
};

export {
    updateQueryParamWithConditionalDebounce,
    updateQueryParam,
    setAllQueryParam,
};
