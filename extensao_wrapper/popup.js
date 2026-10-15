document.getElementById("extrair").addEventListener("click", async () => {
    const resultado = document.getElementById("resultado");
    resultado.textContent = "Extraindo pedido...";

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

        // 1. Extrai os dados da página
        const resposta = await chrome.tabs.sendMessage(aba.id, {
            action: "extrairComprador"
        });

        if (!resposta.success) {
            throw new Error(resposta.error);
        }

        const payload = resposta.data;

        // 2. Exibe o payload extraído
        resultado.textContent =
            "Pedido extraído!\nEnviando para a API...";

        // 3. Envia o payload para o FastAPI
        const retornoApi = await enviarParaApi(payload);

        // 4. Exibe a resposta do backend
        resultado.textContent = JSON.stringify({
            payload,
            resposta_api: retornoApi
        }, null, 2);

    } catch (error) {
        resultado.textContent = `Erro: ${error.message}`;
    }
});

async function enviarParaApi(payload) {
    const resposta = await fetch(
        "http://127.0.0.1:8000/nfe",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        }
    );

    const texto = await resposta.text();

    let resultado;

    try {
        resultado = texto ? JSON.parse(texto) : {};
    } catch {
        resultado = { detail: texto };
    }

    if (!resposta.ok) {
        throw new Error(
            JSON.stringify(resultado.detail ?? resultado)
        );
    }

    return resultado;
}
