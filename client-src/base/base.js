// TODO: factor out list of supported language
//
const languages = ["en", "de", "es", "fr", "cs"];

function setLanguage(lang) {
    const path = window.location.pathname.slice(1); // remove first slash
    const parts = path.split("/");
    if (languages.includes(parts[0])) {
        // overwrite
        parts[0] = lang;
    } else {
        // prepend
        parts.unshift(lang);
    }
    // remove trailing slash
    window.location.pathname = parts.join("/").replace(/\/$/, "");
}

for (let i = 0; i < languages.length; i++) {
    document.getElementById(`lang_${languages[i]}`).onclick = () => setLanguage(languages[i]);
}
