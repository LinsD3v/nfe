# Potato Commander 🥔

Automação local para capturar dados de pedidos do Mercado Livre, organizá-los em uma fila e, como objetivo futuro, apoiar a emissão de notas fiscais eletrônicas (NF-e) por meio da automação do sistema emissor.

> **Estado do projeto: beta em desenvolvimento.** A captura pelo navegador, a API e o armazenamento local já têm uma primeira implementação. A emissão da NF-e ainda não foi implementada: atualmente, o worker busca pedidos elegíveis e muda seu status para `processing`, mas ainda não chama a automação do emissor nem confirma o resultado da emissão.

## Objetivos

- Reduzir a transcrição manual de dados dos pedidos.
- Receber dados capturados no Mercado Livre por uma extensão do Chrome.
- Validar e registrar cada pedido localmente, evitando registros duplicados.
- Impedir o encaminhamento automático de pedidos que precisam de tratamento, como pedidos com mais de um pacote.
- Evoluir para um worker que interaja com o sistema emissor e registre o resultado para consulta e auditoria.

O projeto não substitui a validação fiscal nem a revisão dos dados. A integração final deverá respeitar as regras fiscais aplicáveis, as permissões de acesso ao Mercado Livre e os procedimentos da operação.

## Visão geral do fluxo

```text
Mercado Livre
    └─> Extensão do Chrome extrai os dados do pedido
         └─> API FastAPI valida e recebe o payload
              └─> SQLite registra o pedido e define sua elegibilidade
                   └─> Worker consulta pedidos pendentes
                        └─> [planejado] automação do emissor, validação e registro da NF-e
```

### Implementado atualmente

1. A extensão identifica o comprador, os itens, o ID da venda e a quantidade de pacotes na página de detalhes do pedido.
2. O popup envia o payload para `POST /nfe` na API local.
3. A API valida os campos com Pydantic e encaminha o pedido ao repositório.
4. O repositório grava o pedido no SQLite. O ID da venda é a chave única, portanto uma nova tentativa não cria outro registro para o mesmo pedido.
5. Pedidos com um pacote são registrados como `pending` e podem ser selecionados pelo worker. Pedidos com mais de um pacote são registrados como `blocked` e não entram na fila automática.
6. O worker muda os pedidos elegíveis encontrados de `pending` para `processing`. A automação de emissão ainda não está conectada.

### Objetivo futuro

O fluxo deverá executar a emissão no sistema fiscal, guardar o número ou identificador da NF-e, atualizar o pedido para `completed` ou `error` e preservar informações úteis para investigar falhas. O reprocessamento, a consulta de status e a operação da fila também precisam ser definidos antes do uso produtivo.

## Componentes

| Componente | Responsabilidade | Situação |
| --- | --- | --- |
| `extensao_wrapper/` | Extrair dados da página e enviar o pedido para a API | Implementação inicial |
| `main.py` | Expor a API HTTP e validar o payload | Implementado |
| `repositories/orders.py` | Registrar pedidos, consultar a fila e atualizar status | Implementado |
| `database.py` e `init_db.py` | Conectar ao SQLite e inicializar a tabela | Implementado |
| `worker/main.py` | Buscar pedidos elegíveis e iniciar o processamento | Parcial; a emissão ainda não está conectada |
| `worker/automations/` | Concentrar futuras etapas de automação do emissor | Ainda sem automações implementadas |
| `worker/AHK/` | Guardar scripts AutoHotkey auxiliares | Estrutura inicial; `open_pdv.ahk` ainda não implementa o fluxo de emissão |
| `worker/JAB/` e `worker/config_dll.py` | Configuração para acesso a aplicações Java via Java Access Bridge | Depende da configuração local |

## Regras atuais dos pedidos

- `order_id` identifica a venda e não pode se repetir no banco.
- `package_count` deve ser maior que zero. Se omitido, assume o valor `1`.
- Se `package_count == 1`, o pedido é registrado com `status = pending` e `should_emit = true`.
- Se `package_count > 1`, o pedido é registrado com `status = blocked` e `should_emit = false`.
- Uma venda já registrada é tratada como duplicada; o registro existente não é substituído.
- O worker consulta somente registros com `status = pending` e `should_emit = true`.

Os status `completed` e `error` fazem parte do fluxo planejado, mas ainda não são atribuídos por uma automação de emissão concluída.

## API

A API local é construída com FastAPI. Enquanto estiver em execução, a documentação interativa fica disponível em `/docs`.

### `GET /life`

Verificação simples de disponibilidade. Retorna:

```json
{
  "message": "Life is good!"
}
```

### `POST /nfe`

Recebe um pedido neste formato:

```json
{
  "order_id": "123456789",
  "package_count": 1,
  "client": {
    "name": "Nome do comprador",
    "cpf": "00000000000",
    "address": "Endereço de entrega"
  },
  "items": [
    {
      "name": "Nome do produto",
      "sku": "SKU-001",
      "quantity": 1,
      "unit_price": "49.90"
    }
  ]
}
```

Validações aplicadas:

- `order_id`, os dados do comprador e os campos dos itens são obrigatórios.
- `items` precisa conter pelo menos um item.
- `quantity`, `unit_price` e `package_count` precisam ser maiores que zero.
- `package_count` é opcional e assume `1` quando omitido.

Exemplo de resposta para um pedido novo elegível:

```json
{
  "Accepted": true,
  "Status": "pending",
  "ShouldEmit": true,
  "PackageCount": 1
}
```

Uma venda duplicada retorna `Accepted: false`, `Reason: "duplicate"` e o status do registro existente. Pedidos com vários pacotes são aceitos para registro, mas retornam `Status: "blocked"` e `ShouldEmit: false`.

## Banco de dados

O banco SQLite é criado como `nfe_data.db` na raiz do projeto. A tabela `nfe_data` armazena:

| Campo | Finalidade |
| --- | --- |
| `order_id` | Identificador único da venda |
| `status` | Situação do pedido na fila |
| `payload` | Dados recebidos em JSON |
| `created_at`, `updated_at` | Datas de criação e atualização |
| `nfe` | Campo reservado para o identificador ou número da nota |
| `error_message` | Campo reservado para detalhes de falha |
| `package_count` | Quantidade de pacotes informada |
| `should_emit` | Indica se o pedido pode seguir para emissão automática |

### Dados pessoais

O payload inclui CPF e endereço. O banco é local e, na implementação atual, não oferece criptografia, controle de acesso, política de retenção ou exclusão automática. Proteja o computador e os arquivos do projeto de acordo com a sensibilidade desses dados. Não publique o banco, payloads reais, capturas de tela com dados de clientes ou logs que revelem informações pessoais.

## Requisitos

- Windows.
- Python compatível com as dependências do projeto. A configuração documentada para o worker usa Python 3.11.
- Google Chrome para carregar a extensão localmente.
- Para a futura automação: sistema emissor instalado e configurado, AutoHotkey v2 quando aplicável e Java Access Bridge/DLL compatível caso o emissor seja uma aplicação Java.

A API e o worker têm arquivos de dependências separados. `worker/worker_requirements.txt` inclui bibliotecas de automação Windows e acesso Java, e possui um conjunto de dependências mais amplo do que o necessário para o worker atual.

### Dependência externa: Java Access Bridge 2.0.2

Os binários do Java Access Bridge **não são distribuídos neste repositório**. Quando essa dependência for necessária, obtenha-a pela [página oficial do Java Access Bridge 2.0.2 da Oracle](https://www.oracle.com/java/technologies/javase-jab-2-0-2-downloads.html), leia e aceite os termos aplicáveis e coloque os arquivos extraídos no diretório local esperado pelo projeto.

A pasta `worker/JAB/accessbridge2_0_2/` contém instruções, não uma cópia dos binários. A configuração da DLL deve apontar para o caminho real do arquivo `WindowsAccessBridge-64.dll` na máquina utilizada. Consulte também `worker/JAB/accessbridge2_0_2/readme.md`.

## Instalação e execução

Execute os comandos abaixo a partir da raiz do repositório, salvo indicação contrária.

### 1. Preparar o banco e o ambiente da API

Crie um ambiente virtual e instale as dependências da API:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python init_db.py
```

Se a política do PowerShell bloquear a ativação, use diretamente o interpretador `.venv\Scripts\python.exe` ou ative o ambiente pelo terminal do VS Code.

### 2. Iniciar a API

Com o ambiente da API ativo, execute na raiz do projeto:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Teste `http://127.0.0.1:8000/life` e acesse `http://127.0.0.1:8000/docs` para consultar os endpoints.

### 3. Carregar a extensão do Chrome

1. Abra `chrome://extensions/` no Chrome e habilite o **Modo do desenvolvedor**.
2. Selecione **Carregar sem compactação** e escolha a pasta `extensao_wrapper/`.
3. Abra uma página de detalhes de venda compatível no Mercado Livre e use o popup da extensão para extrair e enviar o pedido.

**Ajuste da integração local:** alinhe a URL usada em `extensao_wrapper/popup.js` com as permissões de host em `extensao_wrapper/manifest.json` (`localhost` ou `127.0.0.1`). Além disso, `main.py` permite CORS para um ID fixo de extensão; ajuste essa origem para o ID exibido pelo Chrome em `chrome://extensions/`. Sem esses alinhamentos, o navegador poderá bloquear a requisição mesmo com a API em execução.

### 4. Preparar e executar o worker

O worker usa um ambiente separado porque suas dependências incluem bibliotecas de automação para Windows e acesso Java:

```powershell
py -3.11 -m venv worker\venv-jab
.\worker\venv-jab\Scripts\python.exe -m pip install -r worker\worker_requirements.txt
```

Se o Java Access Bridge for necessário, configure em `worker/config_dll.py` o caminho real para `WindowsAccessBridge-64.dll`. A configuração atual pode apontar para um caminho absoluto de outra máquina; ajuste-a antes de executar.

Para executar a rotina existente, a partir da raiz do repositório:

```powershell
.\worker\venv-jab\Scripts\python.exe -m worker.main
```

> **Importante:** essa rotina ainda não emite NF-e. No estado atual, os pedidos elegíveis encontrados são marcados como `processing`. O arquivo `worker/startup_worker.bat` referencia `worker.startup_worker`; como esse módulo não aparece na estrutura documentada, confirme ou corrija essa referência antes de usar o launcher.

## Limitações conhecidas

- A API escuta localmente. Não a exponha à rede ou à internet sem autenticação, autorização, proteção de dados e configuração de CORS adequadas.
- A extração depende dos seletores e textos atuais da página do Mercado Livre. Mudanças no site podem interrompê-la; valide os dados antes de qualquer emissão.
- A permissão de host da extensão declara atualmente `localhost`, enquanto o popup faz o `fetch` para `127.0.0.1`. As configurações precisam concordar.
- A origem CORS da API está fixa em um ID de extensão. O ID da extensão carregada localmente precisa corresponder, ou a configuração precisa ser atualizada.
- O worker ainda não tem bloqueio atômico da fila para execuções concorrentes, retentativas, timeout, verificação do resultado ou recuperação de pedidos deixados em `processing`.
- A automação fiscal dependerá do emissor, do formato dos dados, dos certificados e das regras da operação. Receber um pedido não significa que a nota tenha sido emitida.

## Próximas etapas sugeridas

1. Tornar a integração da extensão configurável e alinhar permissões, URL da API e CORS.
2. Validar os dados extraídos e apresentar uma revisão explícita antes de colocar os pedidos na fila de emissão.
3. Definir transições de status, concorrência da fila, retentativas e recuperação após falhas.
4. Implementar a automação do emissor em etapas pequenas e verificáveis, validando cada tela e cada resultado.
5. Persistir o número ou a chave da NF-e e os erros técnicos, além de permitir consulta do histórico por venda.
6. Adicionar testes para validação do payload, duplicidade, regra de pacotes, persistência e processamento do worker.
7. Definir controles para proteção, acesso, retenção e descarte de CPF e endereço.

## Estrutura do repositório

```text
.
├── main.py                         # API FastAPI
├── database.py                     # Conexão SQLite
├── init_db.py                      # Criação da tabela
├── repositories/
│   └── orders.py                   # Persistência e regras da fila
├── extensao_wrapper/
│   ├── manifest.json               # Manifesto da extensão Chrome
│   ├── content.js                  # Extração dos dados da página
│   ├── popup.html
│   └── popup.js                    # Envio do payload para a API
└── worker/
    ├── main.py                     # Processamento inicial da fila
    ├── config_dll.py               # Configuração do Java Access Bridge
    ├── automations/                # Futuras automações do emissor
    ├── AHK/                        # Scripts AutoHotkey auxiliares
    ├── JAB/
    │   └── accessbridge2_0_2/
    │       └── readme.md            # Instruções para obter a dependência
    └── worker_requirements.txt     # Dependências do worker
```

---

**Potato Commander** — beta em desenvolvimento. Contribuições e sugestões são bem-vindas; recursos descritos como planejados ainda não devem ser considerados prontos para uso produtivo.
