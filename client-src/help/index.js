import { closeAllDetailsElements, openAllDetailsElements, openDetailsParents } from "../shared";

// open details sections when anchor link is used

// if opened from other page
const anchor = document.location.hash;
if (anchor) {
    openDetailsParents(document.querySelector(anchor));
}

// jump inside page
[...document.querySelectorAll("[href^='#']")].forEach((anchorLink) => {
    const anchorHref = anchorLink.getAttribute("href");
    const onClick = () => {
        closeAllDetailsElements();
        openDetailsParents(document.querySelector(anchorHref));
    };
    anchorLink.addEventListener("click", onClick);
});

window.printPage = () => {
    openAllDetailsElements();
    window.print();
    closeAllDetailsElements();
};
