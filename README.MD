# Potato Commander

Automação local para capturar dados de pedidos no Mercado Livre, organizar esses dados em uma fila e, como objetivo do projeto, apoiar a emissao de notas fiscais eletronicas (NF-e) por meio de automacao do sistema emissor.

> **Estado do projeto:** a captura pelo navegador, a API e o armazenamento local ja possuem uma primeira implementacao. A emissao da NF-e ainda e uma etapa planejada: o worker atual apenas busca pedidos pendentes e atualiza seu status para `processing`; a chamada da automacao e a confirmacao do resultado ainda nao existem.

## Objetivos

- Reduzir a transcricao manual de dados de pedidos.
- Receber os dados capturados no Mercado Livre por uma extensao do Chrome.
- Validar e registrar cada pedido localmente, evitando duplicidades.
- Impedir a emissao automatica em casos que ainda precisam de tratamento, como pedidos com mais de um pacote.
- Evoluir para um worker que emita a NF-e no sistema utilizado pela operacao e registre o resultado para consulta e auditoria.

O projeto nao substitui a validacao fiscal ou a revisao de dados. A integracao final deve respeitar as regras fiscais aplicaveis, as permissoes de acesso ao Mercado Livre e os procedimentos da empresa.

## Visao do fluxo

```text
Mercado Livre
		-> Extensao Chrome extrai os dados do pedido
		-> API FastAPI valida e recebe o payload
		-> SQLite registra o pedido e define sua elegibilidade
		-> Worker consulta pedidos pendentes
		-> [planejado] automacao do emissor, validacao e registro da NF-e
```

### Implementado hoje

1. A extensao identifica o comprador, os itens, o ID da venda e a quantidade de pacotes na pagina de detalhes do pedido.
2. O popup envia o payload para `POST /nfe` na API local.
3. A API valida os campos com Pydantic e encaminha o pedido ao repositorio.
4. O repositorio grava o pedido no SQLite. O ID da venda e a chave unica, portanto uma segunda tentativa nao cria outro registro.
5. Pedidos com um pacote ficam como `pending` e podem ser selecionados pelo worker. Pedidos com mais de um pacote ficam como `blocked` e nao entram na fila automatica.
6. O worker muda os pedidos encontrados de `pending` para `processing`. A automacao de emissao esta pendente.

### Visao de chegada

O fluxo futuro deve concluir a emissao no sistema fiscal, guardar o numero ou identificador da NF-e, atualizar o pedido para `completed` ou `error` e preservar uma mensagem de erro que permita investigar falhas. Reprocessamento, consulta de status e operacao da fila tambem devem ser definidos antes de uso produtivo.

## Componentes

| Componente | Responsabilidade | Situacao |
| --- | --- | --- |
| `extensao_wrapper/` | Extrair os dados da pagina e enviar o pedido para a API | Implementacao inicial |
| `main.py` | Expor a API HTTP e validar o payload | Implementado |
| `repositories/orders.py` | Registrar pedidos, consultar a fila e atualizar status | Implementado |
| `database.py` e `init_db.py` | Conectar e inicializar o SQLite | Implementado |
| `worker/main.py` | Buscar pedidos elegiveis e iniciar o processamento | Parcial; emissao ainda nao conectada |
| `worker/automations/` | Concentrar as etapas de automacao do sistema emissor | Sem automacoes implementadas no momento |
| `worker/AHK/` | Scripts AutoHotkey auxiliares | Estrutura inicial; `open_pdv.ahk` ainda nao define a automacao |
| `worker/JAB/` e `worker/config_dll.py` | Acesso a aplicacoes Java via Java Access Bridge | Dependente de configuracao local |

## Regras atuais dos pedidos

- `order_id` identifica a venda e nao pode se repetir no banco.
- `package_count` deve ser maior que zero; se omitido, assume `1`.
- Um pedido com `package_count == 1` e registrado com `status = pending` e `should_emit = true`.
- Um pedido com mais de um pacote e registrado com `status = blocked` e `should_emit = false`.
- Uma venda ja registrada e recusada como duplicada; o registro existente nao e substituido.
- O worker consulta apenas registros com status `pending` e `should_emit = true`.

Os status `completed` e `error` estao previstos no fluxo, mas ainda nao sao atribuidos por uma automacao concluida.

## Contrato da API

### `GET /life`

Verificacao simples de disponibilidade. Retorna:

```json
{"message": "Life is good!"}
```

### `POST /nfe`

Recebe um pedido no seguinte formato:

```json
{
	"order_id": "123456789",
	"package_count": 1,
	"client": {
		"name": "Nome do comprador",
		"cpf": "00000000000",
		"address": "Endereco de entrega"
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

Validacoes aplicadas: `order_id`, dados do comprador e campos do item sao obrigatorios; `items` precisa ter ao menos um item; `quantity`, `unit_price` e `package_count` precisam ser maiores que zero. `package_count` e opcional e assume `1`.

Pedido novo aceito:

```json
{
	"Accepted": true,
	"Status": "pending",
	"ShouldEmit": true,
	"PackageCount": 1
}
```

Uma venda duplicada retorna `Accepted: false`, `Reason: "duplicate"` e o status do registro existente. Um pedido com varios pacotes e aceito para registro, mas retorna status `blocked` e `ShouldEmit: false`.

A documentacao interativa do FastAPI fica disponivel em `/docs` enquanto a API estiver em execucao.

## Modelo de dados

O banco e criado como `nfe_data.db` na raiz do projeto. A tabela `nfe_data` armazena:

| Campo | Uso |
| --- | --- |
| `order_id` | Identificador unico da venda |
| `status` | Situacao do pedido na fila |
| `payload` | Dados recebidos em JSON |
| `created_at`, `updated_at` | Datas de criacao e atualizacao |
| `nfe` | Reservado para o identificador/numero da nota |
| `error_message` | Reservado para detalhes de falha |
| `package_count` | Quantidade de pacotes informada |
| `should_emit` | Indica se o pedido pode seguir para emissao automatica |

O payload inclui CPF e endereco. O banco e local e nao implementa criptografia, controle de acesso, politica de retencao ou exclusao automatica; proteja o computador e os arquivos do projeto de acordo com a sensibilidade desses dados.

## Requisitos

- Windows.
- Python compativel com as dependencias do projeto. A configuracao do Java Access Bridge cita Python 3.10 ou 3.11 para o worker.
- Google Chrome para carregar a extensao local.
- Para a futura automacao: sistema emissor instalado e configurado, AutoHotkey v2 quando aplicavel e Java Access Bridge/DLL compativel quando o emissor for uma aplicacao Java.

A API e o worker possuem arquivos de dependencias separados. O `worker/worker_requirements.txt` contem dependencias de automacao mais amplas do que as usadas pelo worker atual.

## Instalacao e execucao

### 1. Preparar o banco

Na raiz do repositorio, crie um ambiente para a API e instale suas dependencias:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python init_db.py
```

Se a politica do PowerShell bloquear a ativacao, use o interpretador diretamente em `.venv\Scripts\python.exe` ou ative o ambiente pelo terminal do VS Code.

### 2. Iniciar a API

Com o ambiente da API ativo, na raiz do projeto:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Teste `http://127.0.0.1:8000/life` e acesse `http://127.0.0.1:8000/docs` para consultar os endpoints.

### 3. Carregar a extensao

1. Abra `chrome://extensions` no Chrome e habilite o **Modo do desenvolvedor**.
2. Escolha **Carregar sem compactacao** e selecione a pasta `extensao_wrapper/`.
3. Abra uma pagina de detalhes de venda compativel no Mercado Livre e use o popup da extensao para extrair e enviar o pedido.

**Ajuste de integracao local:** antes de testar, alinhe a URL usada em `extensao_wrapper/popup.js` com as permissoes de host do `extensao_wrapper/manifest.json` (`localhost` ou `127.0.0.1`). Alem disso, o `main.py` permite CORS para um ID fixo de extensao; configure essa origem para o ID mostrado pelo Chrome em `chrome://extensions`. Sem esses alinhamentos, o navegador pode bloquear a requisicao mesmo com a API no ar.

### 4. Preparar e executar o worker

O worker usa um ambiente separado porque suas dependencias incluem bibliotecas de automacao Windows e acesso Java:

```powershell
py -3.11 -m venv worker\venv-jab
.\worker\venv-jab\Scripts\python.exe -m pip install -r worker\worker_requirements.txt
```

Configure em `worker/config_dll.py` o caminho real para `WindowsAccessBridge-64.dll` se o Java Access Bridge for necessario. A configuracao atual aponta para um caminho absoluto de outra pasta/maquina.

Para executar a rotina existente, na raiz:

```powershell
.\worker\venv-jab\Scripts\python.exe -m worker.main
```

**Importante:** essa rotina ainda nao emite NF-e. No momento, pedidos elegiveis sao marcados como `processing`. O launcher `worker/startup_worker.bat` tambem referencia `worker.startup_worker`; confirme esse modulo antes de usar o launcher, pois o arquivo nao aparece na estrutura atual do projeto.

## Configuracao e limites conhecidos

- A API escuta localmente; nao a exponha na rede ou na internet sem autenticacao, autorizacao, protecao de dados e configuracao de CORS apropriadas.
- O scraper depende dos seletores e textos atuais da pagina do Mercado Livre. Mudancas no site podem interromper a extracao; valide os dados antes de qualquer emissao.
- A permissao de host da extensao atualmente declara `localhost`, enquanto o popup faz o `fetch` para `127.0.0.1`. As duas configuracoes precisam concordar.
- A origem CORS da API esta fixa em um ID de extensao. O ID da extensao carregada localmente precisa corresponder ou a configuracao precisa ser atualizada.
- O worker nao possui, ainda, bloqueio atomico da fila para execucoes concorrentes, retentativas, timeout, verificacao de resultado ou recuperacao de pedidos deixados em `processing`.
- A automacao fiscal depende do emissor, do leiaute dos dados, dos certificados e das regras da operacao. Nenhuma dessas etapas deve ser considerada concluida apenas pela recepcao do pedido.

## Proximas etapas sugeridas

1. Tornar a integracao da extensao configuravel e alinhar permissoes, URL da API e CORS.
2. Validar os dados extraidos e apresentar uma revisao explicita antes de enfileirar pedidos para emissao.
3. Definir transicoes de status, concorrencia da fila, retentativas e recuperacao apos falha.
4. Implementar a automacao do emissor em etapas pequenas e verificaveis, com validacao de cada tela/resultado.
5. Persistir numero/chave da NF-e e erros tecnicos, e permitir consulta do historico por venda.
6. Adicionar testes para validacao do payload, duplicidade, regra de pacotes, persistencia e processamento do worker.
7. Definir controles para protecao, acesso, retencao e descarte de CPF e endereco.

## Estrutura do repositorio

```text
.
|-- main.py                      # API FastAPI
|-- database.py                  # Conexao SQLite
|-- init_db.py                   # Criacao da tabela
|-- repositories/
|   `-- orders.py                # Persistencia e regras da fila
|-- extensao_wrapper/
|   |-- manifest.json            # Manifesto da extensao Chrome
|   |-- content.js               # Extracao dos dados da pagina
|   |-- popup.html
|   `-- popup.js                  # Envio do payload para a API
`-- worker/
		|-- main.py                   # Processamento inicial da fila
		|-- config_dll.py             # Configuracao Java Access Bridge
		|-- automations/              # Futuras automacoes do emissor
		|-- AHK/                      # Scripts AutoHotkey
		`-- worker_requirements.txt   # Dependencias do worker
```
