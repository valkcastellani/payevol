# payEvol - Evolução Salarial

## Visão Geral
O payEvol é uma aplicação web interativa para análise da evolução do poder de compra de salários no Brasil, desde julho de 1994 até o mês anterior ao atual. A ferramenta compara diferentes métodos de atualização salarial: múltiplos do salário mínimo, correção pelo IPCA, pelo INPC e comparação direta com o salário atual informado pelo usuário.

## Funcionalidades
- **Simulação de evolução salarial**: informe um salário de referência (mês/ano) e veja sua evolução ao longo do tempo.
- **Comparação por múltiplos do salário mínimo**: calcula o valor equivalente mantendo o mesmo número de salários mínimos ao longo dos anos.
- **Correção monetária pelo IPCA e INPC**: atualiza o valor informado conforme a inflação oficial.
- **Comparação com salário atual**: opcionalmente, compare o salário atual informado com os valores corrigidos.
- **Visualização interativa**: gráficos e tabelas mensais, com legendas e tooltips em português.

## Como funciona
1. O usuário seleciona o mês/ano de referência (a partir de 07/1994) e informa o salário.
2. O app busca automaticamente as séries históricas de salário mínimo, IPCA e INPC.
3. Os valores são calculados e exibidos em gráficos e tabelas, permitindo fácil comparação.

## Técnicas e Fontes de Dados
### Webscraping e APIs
- **Salário Mínimo**: obtido via webscraping da página [Previdenciarista](https://previdenciarista.com/tabela-historica-dos-salarios-minimos/) usando `requests` e `pandas.read_html`. Se necessário, faz fallback para regex no HTML.
- **IPCA e INPC**: obtidos diretamente das APIs públicas do IBGE/SIDRA (JSON), garantindo dados oficiais e atualizados. Para o INPC, se a série principal não estiver disponível, reconstrói a série a partir da variação mensal.

### Principais bibliotecas
- [Streamlit](https://streamlit.io/) — interface web interativa
- [Altair](https://altair-viz.github.io/) — gráficos customizados
- [Pandas](https://pandas.pydata.org/) — manipulação de dados
- [Requests](https://docs.python-requests.org/) — acesso HTTP

## Instalação e Uso Local
1. **Clone o repositório:**
  ```bash
  git clone https://github.com/valkcastellani/payevol.git
  cd payevol
  ```
2. **(Opcional, porém recomendado) Crie um ambiente virtual:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
3. **Instale as dependências:**
  ```bash
  pip install -r requirements.txt
  ```
4. **Execute o app:**
  ```bash
  streamlit run app.py
  ```
5. **Acesse pelo navegador:**
  O endereço local será exibido (ex: http://localhost:8501).

## Uso Online
Acesse diretamente sem instalar nada:
👉 [payevol.streamlit.app](https://payevol.streamlit.app)

## Licença
MIT License — © 2025–2026 Valk Luiz de Oliveira Castellani

## Contato
- [LinkedIn](https://www.linkedin.com/in/valkcastellani)
- [GitHub](https://github.com/valkcastellani)

Dúvidas ou sugestões? Abra uma issue ou entre em contato!
