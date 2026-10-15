function extrairComprador() {
    const cartao = [...document.querySelectorAll(".billing-info-card")]
        .find(el => el.innerText.includes("Dados do comprador"));

    if (!cartao) {
        throw new Error("Não foi possível encontrar o cartão de dados do comprador.");
    }

    const name = cartao
        .querySelector(".billing-info-card__content span")
        ?.textContent.trim();

    if (!name) {
        throw new Error("Não foi possível encontrar o nome do comprador.");
    }

    return { name }

}


chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "extrairComprador") return;

    try {
        sendResponse({
            success: true,
            data: extrairComprador()
        });
    } catch (error) {
        sendResponse({
            success: false,
            error: error.message
        });
    }
});