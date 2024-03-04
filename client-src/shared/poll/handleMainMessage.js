/**
 * Resolve handler to update the main message on the page when all tasks finished,
 *     either successful, partly successful or completely failed
 *     The function assumes a text container element with the id "main-message"
 * @param responses
 */
function handleMainMessage(responses) {
    const element = document.querySelector("#main-message");
    element.querySelector(".pending").classList.toggle("hidden");
    if (responses.every((response) => response.status === 200)) {
        element.querySelector(".success").classList.toggle("hidden");
    } else if (responses.some((response) => response.status === 200)) {
        element.querySelector(".partial-success").classList.toggle("hidden");
    } else {
        element.querySelector(".error").classList.toggle("hidden");
    }
}

export {
    handleMainMessage,
};
