/**
 * Resolve handler to update the main message on the page when all tasks finished,
 *     either successful, partly successful or completely failed
 *     The function assumes a text container element with the id "main-message"
 * @param responses
 */
function handleMainMessage(responses) {
    if (responses.every((response) => response.status === 200)) {
        document.getElementById("main-message")
            .innerText = "Your results are ready for download!";
    } else if (responses.some((response) => response.status === 200)) {
        document.getElementById("main-message")
            .innerText = "Sorry. "
            + "Only some of your results could be generated for download.";
    } else {
        document.getElementById("main-message")
            .innerText = "Your results should have been downloadable from here, "
            + "but we are having troubles on our servers!";
    }
}

export {
    handleMainMessage,
};
