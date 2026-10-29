# NotaFácil API

API REST em Django para o app mobile **NotaFácil** (gestão de notas fiscais e garantias de produtos).
Consumida por um app React Native/Expo em TypeScript.

**Stack:** Python 3.11+, Django 5, Django REST Framework, autenticação por Token, PostgreSQL,
django-cors-headers, Pillow (fotos) e drf-spectacular (Swagger).

---

## 1. Instalação

### Criar e ativar o ambiente virtual

**Windows (PowerShell ou CMD):**

```bash
python -m venv .venv
.venv\Scripts\activate
```

> Se o PowerShell bloquear o script de ativação, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Mac / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Com o ambiente ativo, o terminal mostra `(.venv)` no início da linha.

### Instalar as dependências

```bash
pip install -r requirements.txt
```

### Criar o banco no PostgreSQL

Com o PostgreSQL instalado e rodando, crie um banco vazio chamado `notafacil`.
Escolha uma das opções:

- **pgAdmin:** clique com o botão direito em *Databases* → *Create* → *Database...* → nome `notafacil`.
- **SQL Shell (psql)** (vem com o instalador do PostgreSQL): entre com o usuário `postgres` e rode:

  ```sql
  CREATE DATABASE notafacil;
  ```

- **Terminal** (se os programas do PostgreSQL estiverem no PATH):

  ```bash
  createdb -U postgres notafacil
  ```

### Configurar a conexão (.env)

Copie o arquivo de exemplo e coloque a senha do seu usuário `postgres`:

```bash
# Mac / Linux
cp .env.example .env
# Windows
copy .env.example .env
```

```ini
DB_NAME=notafacil
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_HOST=localhost
DB_PORT=5432
```

> O `.env` está no `.gitignore`: a senha **não** vai para o repositório.

### Criar as tabelas e os dados de demonstração

```bash
python manage.py migrate
python manage.py seed_demo
```

---

## 2. Como rodar

```bash
python manage.py runserver 0.0.0.0:8000
```

O `0.0.0.0` faz a API aceitar conexões de outros aparelhos da rede (celular, emulador),
e não só do próprio computador.

- API: http://localhost:8000/api/
- Documentação Swagger: http://localhost:8000/api/docs/
- Schema OpenAPI: http://localhost:8000/api/schema/
- Admin do Django: http://localhost:8000/admin/ (crie um usuário com `python manage.py createsuperuser`)

### Descobrir o IP da máquina na rede

| Sistema | Comando | Onde olhar |
|---|---|---|
| Windows | `ipconfig` | "Endereço IPv4" do adaptador Wi-Fi (ex.: `192.168.0.15`) |
| Mac | `ipconfig getifaddr en0` (ou `ifconfig`) | IP após `inet` na interface `en0` |
| Linux | `hostname -I` (ou `ifconfig` / `ip a`) | IP da interface Wi-Fi |

Qual endereço o app deve usar:

| Onde o app roda | URL da API |
|---|---|
| Celular físico (Expo Go) | `http://IP_DA_MAQUINA:8000` (ex.: `http://192.168.0.15:8000`) |
| Emulador Android | `http://10.0.2.2:8000` (atalho do emulador para o computador) |
| Simulador iOS / navegador | `http://localhost:8000` |

> O celular e o computador precisam estar **na mesma rede Wi-Fi**.

### Firewall do Windows

Se o celular não conseguir acessar, libere a porta 8000. Abra o **PowerShell como administrador** e rode:

```powershell
netsh advfirewall firewall add rule name="Django 8000" dir=in action=allow protocol=TCP localport=8000
```

(Ou aceite o aviso "Permitir acesso" do Firewall na primeira vez que rodar o servidor, marcando **Redes privadas**.)

### Variáveis de ambiente (opcionais)

Ficam no arquivo `.env`. Todas têm um valor padrão para desenvolvimento:

| Variável | Padrão | Uso |
|---|---|---|
| `DB_NAME` | `notafacil` | Nome do banco no PostgreSQL |
| `DB_USER` | `postgres` | Usuário do banco |
| `DB_PASSWORD` | (vazio) | Senha do usuário do banco |
| `DB_HOST` | `localhost` | Endereço do servidor PostgreSQL |
| `DB_PORT` | `5432` | Porta do PostgreSQL |
| `DJANGO_SECRET_KEY` | chave de dev | Troque em produção |
| `DJANGO_DEBUG` | `True` | `False` em produção |
| `DJANGO_ALLOWED_HOSTS` | `*` | Lista separada por vírgula |
| `DJANGO_CORS_ALLOW_ALL` | igual a `DEBUG` | Libera CORS para qualquer origem |

---

## 3. Usuário de demonstração

O comando `python manage.py seed_demo` cria (ou recria):

- **Usuário:** `aluno`
- **Senha:** `senac123`
- 6 notas de exemplo (TV, notebook, geladeira, máquina de lavar, celular e fone) com datas
  calculadas a partir de hoje, para sempre aparecerem os três status: **vigente**, **vencendo** e **vencida**.

Pode rodar quantas vezes quiser: as notas do `aluno` são apagadas e criadas de novo.

---

## 4. Endpoints

Todas as rotas começam com `/api/`. As rotas de notas exigem o header
`Authorization: Token <token>`.

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| POST | `/api/auth/registro/` | não | Cria usuário `{username, password}` e devolve `{token}` |
| POST | `/api/auth/login/` | não | Devolve `{token}` |
| GET | `/api/auth/eu/` | sim | Devolve `{id, username}` do dono do token |
| GET | `/api/notas/` | sim | Lista as notas do usuário (`?busca=` e `?status=`) |
| POST | `/api/notas/` | sim | Cria nota (JSON ou multipart com foto) |
| GET | `/api/notas/{id}/` | sim | Detalhe |
| PUT / PATCH | `/api/notas/{id}/` | sim | Edita (pode trocar a foto) |
| DELETE | `/api/notas/{id}/` | sim | Remove a nota e o arquivo da foto |

Filtros da listagem:

- `?busca=texto` → procura na descrição do produto ou na loja
- `?status=vigente|vencendo|vencida`

### Formato de uma nota (JSON)

```json
{
  "id": 1,
  "descricaoProduto": "Smart TV Samsung 55\"",
  "fotoUri": "http://192.168.0.15:8000/media/notas/tv.jpg",
  "dataCompra": "18/07/2026",
  "tempoGarantiaMeses": 12,
  "loja": "Magazine Luiza",
  "assistenciaTecnica": "Assistência autorizada Samsung",
  "dataVencimento": "18/07/2027",
  "statusGarantia": "vigente"
}
```

- `dataCompra` aceita `dd/mm/aaaa` ou `aaaa-mm-dd` e sempre volta em `dd/mm/aaaa`.
- `dataVencimento` e `statusGarantia` são calculados (somente leitura). A regra fica em
  `notas/garantia.py`, espelhando o `utils/garantia.ts` do app: **vencendo** quando faltam 30 dias ou menos.
- `fotoUri` volta como URL completa (ou `null`). Para enviar foto use multipart (máx. 5 MB).
  Num PUT/PATCH em JSON, reenviar a URL atual mantém a foto; enviar `null` remove a foto.

### Formato dos erros

Sempre em português, em um destes formatos (o app lê a primeira mensagem):

```json
{ "username": ["Este usuário já existe."] }
```

```json
{ "detail": "Usuário ou senha inválidos." }
```

Token ausente ou inválido → **401**. Nota de outro usuário → **404**.

---

## 5. Exemplos com curl

> No Windows, use o **Git Bash** para copiar os comandos como estão
> (no PowerShell, troque `curl` por `curl.exe` e ajuste as aspas).

```bash
API=http://localhost:8000/api
```

**Registro**

```bash
curl -X POST $API/auth/registro/ \
  -H "Content-Type: application/json" \
  -d '{"username": "maria", "password": "123456"}'
# {"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
```

**Login**

```bash
curl -X POST $API/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "aluno", "password": "senac123"}'
```

Guarde o token numa variável para os próximos comandos:

```bash
TOKEN=cole_o_token_aqui
```

**Listar (com filtros opcionais)**

```bash
curl $API/notas/ -H "Authorization: Token $TOKEN"
curl "$API/notas/?status=vencendo" -H "Authorization: Token $TOKEN"
curl "$API/notas/?busca=samsung" -H "Authorization: Token $TOKEN"
```

**Criar (JSON, sem foto)**

```bash
curl -X POST $API/notas/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricaoProduto": "Air Fryer Mondial", "dataCompra": "05/09/2026", "tempoGarantiaMeses": 12, "loja": "Americanas"}'
```

**Criar com foto (multipart)**

```bash
curl -X POST $API/notas/ \
  -H "Authorization: Token $TOKEN" \
  -F "descricaoProduto=Celular Motorola Edge" \
  -F "dataCompra=01/10/2026" \
  -F "tempoGarantiaMeses=12" \
  -F "loja=Fast Shop" \
  -F "fotoUri=@/caminho/da/nota.jpg"
```

**Editar (PATCH altera só os campos enviados)**

```bash
curl -X PATCH $API/notas/1/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"loja": "Magazine Luiza", "tempoGarantiaMeses": 24}'
```

**Trocar a foto**

```bash
curl -X PATCH $API/notas/1/ \
  -H "Authorization: Token $TOKEN" \
  -F "fotoUri=@/caminho/da/nova-foto.jpg"
```

**Apagar**

```bash
curl -X DELETE $API/notas/1/ -H "Authorization: Token $TOKEN"
# resposta 204 (sem conteúdo)
```

---

## 6. Testes

```bash
python manage.py test
```

O Django cria um banco temporário `test_notafacil` e o apaga no final, então o usuário
do `.env` precisa ter permissão para criar bancos (o `postgres` tem).

Os testes cobrem registro, login, `/auth/eu/`, 401 sem token / token inválido, CRUD, isolamento entre usuários,
formato de data, cálculo do status da garantia e upload de foto.

---

## 7. Estrutura do projeto

```
config/            # configurações do projeto (settings, urls)
notas/
  models.py        # modelo Nota
  garantia.py      # regras de vencimento/status (espelho do utils/garantia.ts)
  serializers.py   # conversão JSON <-> modelo (camelCase) e validações
  views.py         # login, registro, eu e o CRUD de notas
  urls.py          # rotas /api/...
  tests.py         # testes automatizados
  management/commands/seed_demo.py   # dados de demonstração
```

---

## 8. Como conectar o app React Native

Crie uma constante com o endereço da API (veja a tabela da seção 2 para escolher o IP):

```ts
// src/services/api.ts
export const API_URL = "http://192.168.0.15:8000/api"; // IP da sua máquina
// Emulador Android: "http://10.0.2.2:8000/api"
```

Login e requisição autenticada com `fetch`:

```ts
import { API_URL } from "./api";

export async function login(username: string, password: string): Promise<string> {
  const resp = await fetch(`${API_URL}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const dados = await resp.json();
  if (!resp.ok) {
    // {"detail": "..."} ou {"campo": ["..."]}: pega a primeira mensagem
    const primeira = dados.detail ?? Object.values(dados)[0]?.[0];
    throw new Error(primeira ?? "Erro ao entrar.");
  }
  return dados.token;
}

export async function listarNotas(token: string) {
  const resp = await fetch(`${API_URL}/notas/`, {
    headers: { Authorization: `Token ${token}` },
  });
  if (resp.status === 401) throw new Error("Sessão expirada. Faça login novamente.");
  return resp.json();
}
```

Enviando uma nota com foto (multipart) a partir de uma imagem do `expo-image-picker`:

```ts
export async function criarNotaComFoto(token: string, fotoUri: string) {
  const form = new FormData();
  form.append("descricaoProduto", "Smart TV");
  form.append("dataCompra", "15/10/2026");
  form.append("tempoGarantiaMeses", "12");
  form.append("loja", "Magazine Luiza");
  form.append("fotoUri", { uri: fotoUri, name: "nota.jpg", type: "image/jpeg" } as any);

  const resp = await fetch(`${API_URL}/notas/`, {
    method: "POST",
    headers: { Authorization: `Token ${token}` }, // não defina Content-Type: o fetch monta o boundary
    body: form,
  });
  return resp.json();
}
```
