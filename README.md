# Corretor OMR — MVP

Aplicação web para correção automática de cartões-resposta (OMR — Optical Mark
Recognition) usando visão computacional com OpenCV.

Fluxo: **Upload → Leitura da folha (OpenCV) → Identificação das marcações →
Comparação com gabarito → Resultado**.

## Estrutura do projeto

```
omr-corrector/
├── backend/
│   ├── app/
│   │   ├── main.py                 # App FastAPI (CORS + rotas)
│   │   ├── api/routes.py           # POST /api/correct, GET /api/health
│   │   ├── omr/
│   │   │   ├── template.py         # CardTemplate (grade de bolhas, 40 questões A-E)
│   │   │   ├── processor.py        # Pipeline OpenCV (grayscale, threshold, contornos,
│   │   │   │                       #   perspectiva, leitura de preenchimento das bolhas)
│   │   │   ├── grading.py          # Comparação com gabarito e estatísticas
│   │   │   ├── visualization.py    # Gera imagem da folha com marcações coloridas
│   │   │   ├── exceptions.py       # Erros tratados (mensagens seguras ao usuário)
│   │   │   └── testdata/
│   │   │       ├── generate_sample.py     # Gera folha de teste sintética
│   │   │       ├── sample_sheet.png       # Folha de teste já gerada
│   │   │       └── sample_answer_key.txt  # Gabarito de teste já gerado
│   │   ├── services/pdf_service.py # Conversão de PDF -> imagem (PyMuPDF)
│   │   ├── models/schemas.py       # Modelos Pydantic da API
│   │   └── utils/answer_key_parser.py  # Parser do texto do gabarito (1-A, 1:A, ...)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/   # Header, AnswerKeyInput, UploadArea, ResultsSummary,
│   │   │                 # ResultsTable, ProcessedImageView, FiducialCard, ErrorBanner
│   │   ├── services/api.ts   # Chamada ao backend (POST /api/correct)
│   │   ├── types/index.ts
│   │   └── App.tsx
│   └── package.json
│
└── README.md
```

## Tecnologias

- **Frontend:** React + TypeScript + Vite
- **Backend:** Python + FastAPI
- **Visão computacional:** OpenCV (grayscale, Gaussian Blur, threshold de Otsu,
  Canny, contornos, correção de perspectiva, morphology, análise de preenchimento)
- **PDF:** PyMuPDF (não depende de binários externos como o Poppler)

## Como instalar

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Como executar

Abra dois terminais.

**Terminal 1 — backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
A API sobe em `http://localhost:8000` (documentação interativa em `/docs`).

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```
A aplicação sobe em `http://localhost:5173` (o Vite já está configurado para
encaminhar chamadas `/api` para `http://localhost:8000`, ver `vite.config.ts`).

Abra `http://localhost:5173` no navegador.

## Como testar

O projeto já inclui uma folha de teste sintética e um gabarito compatível em
`backend/app/omr/testdata/`:

- `sample_sheet.png` — folha de resposta preenchida (40 questões, template padrão)
- `sample_answer_key.txt` — gabarito correspondente

Para testar pela interface:
1. Abra a aplicação (`http://localhost:5173`).
2. Copie o conteúdo de `backend/app/omr/testdata/sample_answer_key.txt` e cole
   no campo de gabarito.
3. Envie o arquivo `backend/app/omr/testdata/sample_sheet.png` na área de upload.
4. Clique em **Corrigir cartão**.
5. O resultado esperado é: **35 corretas, 3 erradas, 1 sem resposta, 1 marcação
   inválida (87,5%)** — esses valores foram conferidos rodando o pipeline
   diretamente durante o desenvolvimento.

Para gerar uma nova folha de teste (com respostas aleatórias diferentes):
```bash
cd backend
source venv/bin/activate
python -m app.omr.testdata.generate_sample
```
Isso sobrescreve `sample_sheet.png` e `sample_answer_key.txt` e imprime no
console quais questões foram propositalmente deixadas em branco, erradas ou
com marcação dupla — útil para validar o algoritmo.

Também é possível testar a API diretamente, sem o frontend:
```bash
curl -X POST http://localhost:8000/api/correct \
  -F "file=@app/omr/testdata/sample_sheet.png" \
  -F "answer_key=$(cat app/omr/testdata/sample_answer_key.txt)"
```

### Usando seu próprio cartão

O template padrão (`default_40`, definido em `backend/app/omr/template.py`)
assume um cartão com **40 questões, alternativas A a E, em 4 colunas de 10
questões**, com a grade de bolhas ocupando aproximadamente da altura 20% a 95%
e da largura 7% a 97% da folha. Se seu cartão físico seguir um layout
diferente, ajuste os parâmetros de `CardTemplate` (`grid_top`, `grid_bottom`,
`grid_left`, `grid_right`, `columns`, `rows_per_column`, `bubble_radius`) para
bater com o seu modelo, ou use o script de geração de folha de teste como
referência visual.

## Critério de confiança da leitura

Para cada questão, o percentual de preenchimento de cada bolha é calculado
(pixels escuros dentro do círculo / área do círculo, após threshold de Otsu).
Os parâmetros ajustáveis estão em `backend/app/omr/processor.py`:

- `FILL_THRESHOLD = 0.35` — preenchimento mínimo para considerar uma bolha
  como marcada. Se nenhuma bolha atingir esse valor, a questão é **sem
  resposta**.
- `AMBIGUITY_MARGIN = 0.12` — se duas ou mais bolhas estão acima do
  threshold e a diferença entre a mais preenchida e a segunda mais preenchida
  é menor que essa margem, a questão é considerada **marcação inválida**.

## Endpoint da API

`POST /api/correct` (multipart/form-data)

Campos:
- `file`: imagem (jpg/jpeg/png) ou PDF do cartão preenchido
- `answer_key`: texto do gabarito (formato `1-A`, `1:A` ou `1) A`, uma questão
  por linha ou separadas por vírgula)
- `template_name` (opcional, padrão `default_40`)

Retorna JSON com `totalQuestions`, `correct`, `wrong`, `blank`, `invalid`,
`score`, a lista `answers` (uma entrada por questão, com `marked`, `correct`,
`status`, `confidence`) e `processedImageBase64` (PNG em base64 da folha com
as marcações destacadas). Para PDFs com múltiplas páginas, o mesmo resultado
também vem detalhado por página em `pages`.

## Simplificações feitas no MVP (conforme escopo definido)

- Um único template de cartão, configurado no backend (sem editor de
  templates na interface) — 40 questões, alternativas A–E, layout em grade.
- Sem autenticação, sem múltiplos usuários, sem persistência em banco de
  dados — cada correção é processada e devolvida na hora, nada é salvo.
- PDF: cada página é convertida em imagem e processada individualmente; não
  há tratamento especial para folhas que ocupem mais de uma página.
- A detecção do contorno do cartão assume que ele é o maior elemento
  retangular/quadrangular da imagem enviada (funciona bem com boa iluminação
  e o cartão ocupando a maior parte do enquadramento).
- A confiança da leitura é heurística (percentual de preenchimento), não um
  modelo de machine learning treinado.

## Limitações conhecidas

- Fotos com iluminação muito irregular, sombras fortes sobre o cartão, ou
  baixa resolução podem reduzir a precisão da leitura.
- Se o cartão não for o maior contorno quadrangular da imagem (por exemplo,
  com muitos objetos ao redor, ou o cartão cortado nas bordas), a detecção
  pode falhar e retornar o erro "cartão não localizado".
- O template atual é fixo (40 questões A–E, 4 colunas). Cartões com layout
  muito diferente precisam de um novo `CardTemplate` (ver seção acima).
- Não há testes automatizados (unitários/integração) no projeto — a validação
  feita durante o desenvolvimento foi executar o pipeline diretamente contra a
  folha de teste sintética e conferir os resultados manualmente.
- PyMuPDF é necessário apenas para suporte a PDF; se não for instalado, o
  endpoint retorna um erro amigável ao tentar processar um PDF (imagens
  jpg/png continuam funcionando normalmente).

## Próximos passos recomendados (P1 / P2, fora do escopo deste MVP)

- P1: melhorar a robustez da correção de perspectiva para fotos tiradas em
  ângulo mais acentuado; permitir ajustar `FILL_THRESHOLD`/`AMBIGUITY_MARGIN`
  pela interface.
- P2: editor de templates de cartão pela interface, cadastro de provas e
  alunos, histórico de correções, exportação para Excel/PDF, banco de dados,
  autenticação e múltiplos usuários, processamento em lote, API pública.
