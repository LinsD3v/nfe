function extrairComprador() {
    const cartao = [...document.querySelectorAll(".billing-info-card")]
        .find(el => el.innerText.includes("Dados do comprador"));

    if (!cartao) {
        throw new Error("Cartão do comprador não encontrado.");
    }

    const campos = {};

    const linhas = cartao.querySelectorAll(
        ".billing-info-card__line"
    );

    for (const linha of linhas) {
        const label = linha
            .querySelector(".billing-info-card__label")
            ?.textContent.trim();

        const valor = linha
            .querySelector(".billing-info-card__content span")
            ?.textContent.trim();

        if (label && valor) {
            campos[label] = valor;
        }
    }

    return {
        name: campos["Nome completo"],
        cpf: campos["CPF"],
        address: campos["Endereço"]
    };
}



function extrairItens() {
    const produtos = document.querySelectorAll(
        ".sc-product-resolutions-wrapper .sc-product"
    );

    if (produtos.length === 0) {
        throw new Error("Nenhum produto encontrado no pedido.");
    }

    return [...produtos].map(produto => {
        const name = produto
            .querySelector(".sc-title a")
            ?.textContent.trim();

        // Procura o texto que contém SKU, sem depender
        // da classe específica do subtítulo.
        const subtitulo = [...produto.querySelectorAll("div, span")]
            .find(el =>
                el.children.length === 0 &&
                /\bSKU\b/i.test(el.textContent)
            )
            ?.textContent.trim();

        const skuMatch = subtitulo?.match(/\bSKU\s+(\S+)/i);

        const precoTexto = produto
            .querySelector(".sc-price__label")
            ?.textContent.trim();

        const quantidadeTexto = produto
            .querySelector(".sc-quantity__value")
            ?.textContent.trim();

        if (!name || !skuMatch || !precoTexto || !quantidadeTexto) {
            throw new Error(
                `Dados incompletos no produto: ${name ?? "nome não encontrado"}`
            );
        }

        const preco = Number(
            precoTexto
                .replace(/[^\d,.-]/g, "")
                .replace(/\./g, "")
                .replace(",", ".")
        );

        const quantidadeMatch = quantidadeTexto.match(/\d+/);

        if (!Number.isFinite(preco) || !quantidadeMatch) {
            throw new Error("Preço ou quantidade inválidos.");
        }

        return {
            name,
            sku: skuMatch[1],
            quantity: Number(quantidadeMatch[0]),
            unit_price: preco.toFixed(2)
        };
    });
}

function extrairIdVenda() {
    const elemento = [...document.querySelectorAll("p.sc-text")]
        .find(el => /\bVenda\s*#\s*\d+/.test(el.textContent));

    const match = elemento?.textContent.match(/\bVenda\s*#\s*(\d+)/);

    if (!match) {
        throw new Error("ID da venda não encontrado.");
    }

    return match[1];
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action !== "extrairComprador") return;

    try {
        sendResponse({
            success: true,
            data: mountPayload()
        });
    } catch (error) {
        sendResponse({
            success: false,
            error: error.message
        });
    }
});


function mountPayload() {
    const idVenda = extrairIdVenda();
    const comprador = extrairComprador();
    const itens = extrairItens();

    const payload = {
        order_id: idVenda,
        client: {
            name: comprador.name,
            cpf: comprador.cpf,
            address: comprador.address
        },
        items: itens
    };

    return payload;
}