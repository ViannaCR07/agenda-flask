# Sistema de Agendamento com Flask

Este projeto é uma aplicação web construída com Flask para controle de agendamentos, com limite de acessos por usuário.

## Funcionalidades

- Login com aprovação por administrador
- Limite de acessos por IP usando Flask-Limiter
- Integração com banco de dados MySQL
- Páginas renderizadas com Jinja2

## Como usar

1. Clone o repositório
2. Crie um ambiente virtual e ative
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Copie o arquivo `.env.example` para `.env` e configure com suas credenciais
5. Execute o projeto:
   ```bash
   python app.py
   ```

## Estrutura

- `app.py`: Aplicação principal
- `database.py`: Conexão com banco de dados
- `templates/`: Páginas HTML
- `static/`: Arquivos CSS/JS

## Licença

Este projeto é livre para uso educacional e pessoal.
