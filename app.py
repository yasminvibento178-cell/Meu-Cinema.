from datetime import date, timedelta
from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, send_from_directory

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "meu_cinema.db"

app = Flask(__name__, template_folder=str(PASTA), static_folder=None)
app.config["SECRET_KEY"] = "chave-meu-cinema"

FILMES = [
    ("Crepúsculo", "12 anos", "Bella Swan se muda para uma pequena cidade e se apaixona por Edward Cullen, um misterioso colega que esconde um segredo sobrenatural.", "2h 02min", 4),
    ("Esquadrão Suicida", "14 anos", "Um grupo de vilões é recrutado para uma perigosa missão em troca de uma possível redução de suas penas.", "2h 03min", 4),
    ("Homem-Aranha", "10 anos", "Após ser picado por uma aranha geneticamente modificada, Peter Parker descobre poderes extraordinários e uma grande responsabilidade.", "2h 01min", 5),
    ("Moana", "Livre", "Uma jovem corajosa parte em uma aventura pelo oceano para salvar seu povo e descobrir o verdadeiro significado de sua identidade.", "1h 47min", 5),
    ("A Odisseia", "12 anos", "Depois da guerra, um herói enfrenta monstros, deuses e tempestades em uma longa jornada de volta para casa.", "2h 10min", 4),
    ("O Diabo Veste Prada", "Livre", "Uma jovem jornalista encara o exigente mundo da moda ao trabalhar como assistente de uma poderosa editora de revista.", "1h 49min", 5),
]


def conectar():
    banco = sqlite3.connect(BANCO)
    banco.row_factory = sqlite3.Row
    return banco


def iniciar_banco():
    banco = conectar()
    banco.execute("""CREATE TABLE IF NOT EXISTS filmes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL UNIQUE,
        classificacao TEXT NOT NULL,
        descricao TEXT NOT NULL,
        duracao TEXT NOT NULL,
        estrelas INTEGER NOT NULL
    )""")
    banco.execute("""CREATE TABLE IF NOT EXISTS ingressos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filme_id INTEGER NOT NULL,
        dia TEXT NOT NULL,
        hora TEXT NOT NULL,
        nome TEXT NOT NULL,
        gmail TEXT NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (filme_id) REFERENCES filmes(id)
    )""")
    banco.executemany("""INSERT OR IGNORE INTO filmes
        (titulo, classificacao, descricao, duracao, estrelas)
        VALUES (?, ?, ?, ?, ?)""", FILMES)
    banco.commit()
    banco.close()


def dias_disponiveis():
    hoje = date.today()
    return [
        (hoje + timedelta(days=numero)).strftime("%d/%m/%Y")
        for numero in range(14)
    ]


def buscar_filmes():
    banco = conectar()
    filmes = banco.execute("SELECT * FROM filmes ORDER BY id").fetchall()
    banco.close()
    return filmes


iniciar_banco()


@app.get("/")
def pagina_inicial():
    filmes = buscar_filmes()
    return render_template(
        "index.html",
        filmes=filmes,
        imagens=[
            "crepusculo.svg",
            "esquadrao-suicida.svg",
            "homem-aranha.svg",
            "moana.svg",
            "a-odisseia.svg",
            "o-diabo-veste-prada.svg",
        ],
        dias=dias_disponiveis(),
        horarios=["13:30", "15:45", "18:00", "20:15", "22:30"],
    )


@app.get("/style.css")
def estilos():
    return send_from_directory(PASTA, "style.css")


@app.get("/img/<nome>")
def imagem(nome):
    return send_from_directory(PASTA / "img", nome)


@app.post("/comprar")
def comprar_ingresso():
    filme_id = request.form.get("filme_id", "").strip()
    dia = request.form.get("dia", "").strip()
    hora = request.form.get("hora", "").strip()
    nome = request.form.get("nome", "").strip()
    gmail = request.form.get("gmail", "").strip()

    if not all([filme_id, dia, hora, nome, gmail]):
        flash("Preencha todos os campos para reservar o ingresso.", "erro")
        return redirect("/#comprar")

    if "@" not in gmail or "." not in gmail.rsplit("@", 1)[-1]:
        flash("Digite um Gmail válido.", "erro")
        return redirect("/#comprar")

    banco = conectar()
    filme = banco.execute(
        "SELECT * FROM filmes WHERE id = ?", (filme_id,)
    ).fetchone()

    if filme is None:
        banco.close()
        flash("Filme não encontrado.", "erro")
        return redirect("/#comprar")

    banco.execute("""INSERT INTO ingressos
        (filme_id, dia, hora, nome, gmail)
        VALUES (?, ?, ?, ?, ?)""", (filme_id, dia, hora, nome, gmail))
    banco.commit()
    banco.close()

    flash(f"Ingresso reservado para {filme['titulo']}!", "sucesso")
    return redirect("/#comprar")


application = app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
