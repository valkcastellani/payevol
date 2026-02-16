# payEvol - Evolução Salarial

## O que é?
O payEvol é uma aplicação web interativa que permite analisar a evolução de salários no Brasil, comparando diferentes métodos de atualização: múltiplos do salário mínimo, ajuste pelo IPCA e INPC, e comparação com o salário atual. A ferramenta é voltada para profissionais, estudantes e interessados em economia, finanças e direito trabalhista.

## Como funciona?
- Você escolhe uma referência de mês/ano (a partir de 07/1994) e informa o salário na referência.
- O app calcula e exibe:
  - O equivalente mantendo o mesmo número de salários mínimos.
  - O valor atualizado pelo IPCA.
  - O valor atualizado pelo INPC (quando disponível).
  - Comparação com o salário atual (opcional).
- Os resultados são apresentados em gráficos interativos e tabelas.

## Técnicas de Webscraping

### Salário Mínimo
- Os dados são obtidos via webscraping da página [Previdenciarista](https://previdenciarista.com/tabela-historica-dos-salarios-minimos/), utilizando `requests` para baixar o HTML e `pandas.read_html` para extrair as tabelas.
- Caso a extração por tabela falhe, utiliza-se regex para buscar os valores diretamente no HTML.

### IPCA e INPC
- Os índices IPCA e INPC são obtidos diretamente das APIs públicas do IBGE/SIDRA, usando requisições HTTP (`requests`) e processamento de JSON.
- Para o INPC, se a API principal não estiver disponível, o app reconstrói a série a partir da variação mensal (também obtida via API), encadeando os valores.

## Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/valkcastellani/payevol.git
cd payevol
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

## Como utilizar

### 1. Execute o aplicativo
```bash
streamlit run app.py
```

### 2. Acesse pelo navegador
O Streamlit irá mostrar o endereço local (ex: http://localhost:8501). Basta acessar e utilizar a interface.

### 3. Utilização online
Você pode acessar diretamente a versão online em:

👉 [payevol.streamlit.app](https://payevol.streamlit.app)

## Principais bibliotecas utilizadas
- streamlit
- pandas
- requests
- lxml
- altair

## Fontes de dados
- Salário mínimo: Previdenciarista
- IPCA e INPC: IBGE/SIDRA

## Licença
Este projeto é open source. Consulte o arquivo LICENSE para mais detalhes.

---

Dúvidas ou sugestões? Abra uma issue ou entre em contato!
