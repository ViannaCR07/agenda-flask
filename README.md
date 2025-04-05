# 📅 Sistema de Agendamento com Flask

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_App-green?logo=flask)](https://flask.palletsprojects.com/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)]()
[![License](https://img.shields.io/badge/licença-MIT-blue)]()

Este projeto é uma aplicação web desenvolvida com **Flask** para controle de agendamentos de turnos, com limite de acessos por IP, autenticação e integração com banco de dados **MySQL**.

---

## ✨ Funcionalidades

- ✅ Login com aprovação por administrador
- ✅ Limite de acessos por IP com Flask-Limiter
- ✅ Agendamento vinculado a turnos, datas e subpraças
- ✅ Integração com banco de dados MySQL
- ✅ Interface web com HTML + Bootstrap

---

## 🚀 Como executar

1. Clone o repositório:

```bash
git clone https://github.com/ViannaCR07/agenda-flask.git
cd agenda-flask
```

2. Crie um ambiente virtual:

```bash
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate    # macOS/Linux
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Copie `.env.example` para `.env` e preencha com os dados do seu banco:

```env
DB_HOST=localhost
DB_USER=usuario
DB_PASSWORD=senha
DB_NAME=nome_do_banco
```

5. Execute o projeto:

```bash
python app.py
```

Acesse no navegador: `http://localhost:5000`

---

## 🖼️ Imagem do sistema (opcional)

> Você pode adicionar aqui um print ou GIF do sistema em uso.

---

## 📁 Estrutura do Projeto

```
agenda-flask/
├── app.py
├── database.py
├── templates/
├── static/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 📌 Tecnologias usadas

- Python 3.10+
- Flask
- MySQL
- HTML/CSS/Bootstrap
- Flask-Limiter
- python-dotenv

---

## 🧑‍💻 Autor

Desenvolvido por **Rodrigo Vianna**  
🔗 [github.com/ViannaCR07](https://github.com/ViannaCR07)

---

## ⚖️ Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
