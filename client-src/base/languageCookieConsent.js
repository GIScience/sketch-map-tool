// For retrieving the selected language across all sub-pages, a cookie is stored (via Flask session)
// Another cookie stores whether this question has already been confirmed to avoid that the user has
// to click ok every time. To be certainly GDPR conform, the user is asked for consent, even though
// there is no tracking etc. involved.

function getConsentToStoreLanguageSelection(lang) {
    if (document.cookie === "languageSet=true" || confirm(
        "If you set a language, cookies are used to store your selection and to apply it on all sub-pages. "
        + "This data is used only to retrieve your selected language and whether you allowed these cookies.\n\n"
        + "Wenn Sie eine Sprache wählen, werden Cookies verwendet, damit sie auf allen "
        + "Unterseiten angewandt wird. Die Cookies werden nur verwendet, um die gewählte Sprache abzufragen und "
        + "abzufragen, ob Sie der Verwendung dieser Cookies zur Sprachauswahl zugestimmt haben.\n\n"
        + "Se você definir um idioma, os cookies serão usados para armazenar sua seleção e aplicá-la em todas as "
        + "subpáginas. Esses dados são usados somente para recuperar o idioma selecionado e para verificar se você "
        + "permitiu esses cookies.\n\n",
    )) {
        document.cookie = "languageSet=true";
        window.location = `/?lang=${lang}`;
    }
}

document.getElementById("lang_en").onclick = () => getConsentToStoreLanguageSelection("en");
document.getElementById("lang_de").onclick = () => getConsentToStoreLanguageSelection("de");
document.getElementById("lang_pt").onclick = () => getConsentToStoreLanguageSelection("pt");
