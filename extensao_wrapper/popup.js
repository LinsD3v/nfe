document.getElementById("extrair").addEventListener("click", async () => {
    const resultado = document.getElementById("resultado");
    resultado.textContent = "Extraindo...";

    try {
        const [aba] = await chrome.tabs.query({
            active: true,
            currentWindow: true
        });

        if (!aba?.id || !aba.url?.startsWith(
            "https://vendedores.mercadolivre.com.br/"
        )) {
            throw new Error("Abra uma página do Mercado Livre.");
        }

        const resposta = await chrome.tabs.sendMessage(aba.id, {
            action: "extrairComprador"
        });

        if (!resposta.success) {
            throw new Error(resposta.error);
        }

        resultado.textContent = JSON.stringify(
            resposta.data,
            null,
            2
        );

    } catch (error) {
        resultado.textContent = `Erro: ${error.message}`;
    }
});
