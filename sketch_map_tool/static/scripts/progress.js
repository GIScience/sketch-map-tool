let continueRefreshing = true;

function reloading() {
    if (continueRefreshing) {
        location.reload();
    }
}
function refresh(timeoutPeriod) {
    setTimeout(() => { reloading(); }, timeoutPeriod);
}

function stopRefresh() {
    continueRefreshing = false;
}

document.addEventListener("DOMContentLoaded", () => {
    refresh(5000);
});
