console.log("HALLO");

function openDetailsParents(element) {
    if (!element) return;

    if (element.nodeName === "DETAILS") {
        element.setAttribute("open", true);
        openDetailsParents(element.parentElement.closest("details"));
    } else {
        openDetailsParents(element.closest("details"));
    }
}

const anchor = document.location.hash;
console.log("anchor", anchor);
if (anchor) {
    openDetailsParents(document.getElementById(anchor));
}
