from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from agenda_marina_pro.models import db, Admin, Servico, Agendamento, Estoque, Financeiro, HorarioFuncionamento, BloqueioData, HorarioEspecial
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_chave_segura'

# =========================
# 🔥 CONFIG BANCO
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://banco_clinica_vn7w_user:FzYVnVsH1snlxs94DMLEnrgYSEma9w97@dpg-d79sbinkijhs73934i6g-a/banco_clinica_vn7w"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# =========================
# 🔐 LOGIN
# =========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# =========================
# 🚀 START APP
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
# =========================
# GERAR HORÁRIOS DINÂMICO (CORRIGIDO)
# =========================
def gerar_horarios(data_obj=None):

    if not data_obj:
        return []

    # 🚫 Bloqueio
    bloqueio = BloqueioData.query.filter_by(data=data_obj, ativo=True).first()
    if bloqueio:
        return []

    dia = data_obj.weekday()

    # 📆 Horário especial
    especial = HorarioEspecial.query.filter(
        HorarioEspecial.data_inicio <= data_obj,
        HorarioEspecial.data_fim >= data_obj,
        HorarioEspecial.dia_semana == dia,
        HorarioEspecial.ativo == True
    ).first()

    if especial:
        inicio_str = especial.inicio   # já é string
        fim_str = especial.fim         # já é string
    else:
        config = HorarioFuncionamento.query.filter_by(
            dia_semana=dia,
            ativo=True
        ).first()

        if not config:
            return []

        inicio_str = config.inicio     # string
        fim_str = config.fim           # string

    horarios = []

    # 🔥 CONVERSÃO CORRETA (ESSA LINHA RESOLVE TUDO)
    inicio = datetime.strptime(inicio_str, "%H:%M")
    fim = datetime.strptime(fim_str, "%H:%M")

    while inicio <= fim:
        horarios.append(inicio.strftime("%H:%M"))
        inicio += timedelta(minutes=30)

    return horarios


# =========================
# BANCO + DADOS INICIAIS
# =========================
with app.app_context():

    db.create_all()

    if not Admin.query.first():
        admin = Admin(
            username="Marinalaia",
            password=generate_password_hash("020820")
        )
        db.session.add(admin)
        db.session.commit()

    if not Servico.query.first():

        servicos = [
            Servico(nome="Design de sobrancelhas com henna", preco=0, duracao=60),
            Servico(nome="Design clássico de sobrancelhas (sem henna)", preco=0, duracao=30),
            Servico(nome="Depilação de buço", preco=0, duracao=10),
            Servico(nome="Brow lamination", preco=0, duracao=90),
            Servico(nome="Lash lifting", preco=0, duracao=90),
            Servico(nome="Aplicação volume brasileiro", preco=0, duracao=120),
            Servico(nome="Aplicação volume brasileiro marrom", preco=0, duracao=120),
            Servico(nome="Aplicação efeito rímel", preco=0, duracao=120),
            Servico(nome="Aplicação volume 5D", preco=0, duracao=120),
            Servico(nome="Aplicação fox eyes", preco=0, duracao=120),
            Servico(nome="Aplicação fox eyes marrom", preco=0, duracao=120),
            Servico(nome="Manutenção volume brasileiro", preco=0, duracao=120),
            Servico(nome="Manutenção volume brasileiro marrom", preco=0, duracao=120),
            Servico(nome="Manutenção efeito rímel", preco=0, duracao=120),
            Servico(nome="Manutenção volume 5D", preco=0, duracao=120),
            Servico(nome="Manutenção fox eyes", preco=0, duracao=120),
            Servico(nome="Manutenção fox eyes marrom", preco=0, duracao=120)
        ]

        db.session.add_all(servicos)
        db.session.commit()

    if not HorarioFuncionamento.query.first():

        horarios = [
            (0, "07:00", "20:00"),
            (1, "07:00", "16:00"),
            (2, "07:00", "16:00"),
            (3, "07:00", "16:00"),
            (4, "07:00", "20:00"),
            (5, "07:00", "20:00"),
            (6, "07:00", "12:00"),
        ]

        for dia, ini, fim in horarios:
            db.session.add(HorarioFuncionamento(
                dia_semana=dia,
                inicio=ini,
                fim=fim,
                ativo=True
            ))

        db.session.commit()


# =========================
# LOGIN
# =========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# =========================
# HOME
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# AGENDAR (COMPLETO E CORRIGIDO)
# =========================
from urllib.parse import quote
from datetime import datetime, timedelta

@app.route("/agendar", methods=["GET", "POST"])
def agendar():

    servicos = Servico.query.all()
    erro = None
    hoje = datetime.now().strftime("%Y-%m-%d")
    agora = datetime.now()

    data_str = request.form.get("data") or request.args.get("data")
    servico_id = request.form.get("servico") or request.args.get("servico")

    data_obj = None
    if data_str:
        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
        except:
            data_obj = None

    # gerar horários
    horarios = gerar_horarios(data_obj)

    # pegar duração do serviço
    duracao = 30
    servico_escolhido = None

    if servico_id:
        servico_escolhido = Servico.query.get(int(servico_id))
        if servico_escolhido:
            duracao = servico_escolhido.duracao

    # bloquear horários passados
    if data_obj and data_obj == agora.date():
        horarios = [
            h for h in horarios
            if datetime.strptime(f"{data_obj} {h}", "%Y-%m-%d %H:%M") > agora
        ]

    # =========================
    # 🔥 VALIDAÇÃO CORRETA DE HORÁRIOS
    # =========================
    if data_obj:

        agendamentos = Agendamento.query.filter_by(data=data_obj).all()
        horarios_validos = []

        for h in horarios:

            inicio_novo = datetime.strptime(f"{data_obj} {h}", "%Y-%m-%d %H:%M")
            fim_novo = inicio_novo + timedelta(minutes=duracao)

            conflito = False

            for ag in agendamentos:
                servico = Servico.query.get(ag.servico_id)
                if not servico:
                    continue

                inicio_existente = datetime.strptime(f"{ag.data} {ag.hora}", "%Y-%m-%d %H:%M")
                fim_existente = inicio_existente + timedelta(minutes=servico.duracao)

                if inicio_novo < fim_existente and fim_novo > inicio_existente:
                    conflito = True
                    break

            if not conflito:
                horarios_validos.append(h)

        horarios = horarios_validos

    # =========================
    # SALVAR AGENDAMENTO
    # =========================
    if request.method == "POST" and request.form.get("hora"):

        nome = request.form.get("nome")
        telefone = request.form.get("telefone")
        hora_str = request.form.get("hora")

        if not (nome and telefone and servico_id and data_str and hora_str):
            erro = "Preencha todos os campos"

        else:

            # BLOQUEAR SE NÃO COUBER NO ÚLTIMO HORÁRIO
            if servico_escolhido and data_obj:

                horarios_dia = gerar_horarios(data_obj)
                ultimo = datetime.strptime(
                    f"{data_obj} {horarios_dia[-1]}",
                    "%Y-%m-%d %H:%M"
                ) + timedelta(minutes=30)

                inicio = datetime.strptime(
                    f"{data_obj} {hora_str}",
                    "%Y-%m-%d %H:%M"
                )

                fim = inicio + timedelta(minutes=servico_escolhido.duracao)

                if fim > ultimo:
                    erro = f"Esse horário não é válido para esse procedimento, pois ele possui duração de {duracao} minutos."
                    return render_template(
                        "agendar.html",
                        servicos=servicos,
                        horarios=horarios,
                        erro=erro,
                        hoje=hoje
                    )

            # 🔒 VALIDAÇÃO FINAL (ANTI-CONFLITO)
            inicio = datetime.strptime(f"{data_obj} {hora_str}", "%Y-%m-%d %H:%M")
            fim = inicio + timedelta(minutes=duracao)

            for ag in Agendamento.query.filter_by(data=data_obj).all():
                servico = Servico.query.get(ag.servico_id)
                if not servico:
                    continue

                inicio_existente = datetime.strptime(f"{ag.data} {ag.hora}", "%Y-%m-%d %H:%M")
                fim_existente = inicio_existente + timedelta(minutes=servico.duracao)

                if inicio < fim_existente and fim > inicio_existente:
                    erro =  "Esse horário não  comporta esse procedimento. Por favor, escolha outro horário."
                    return render_template(
                        "agendar.html",
                        servicos=servicos,
                        horarios=horarios,
                        erro=erro,
                        hoje=hoje
                    )

            novo = Agendamento(
                cliente_nome=nome,
                telefone=telefone,
                servico_id=int(servico_id),
                data=data_obj,
                hora=hora_str,
                status="Pendente"
            )

            db.session.add(novo)
            db.session.commit()
            # =========================
            # WHATSAPP AUTOMÁTICO (CORRIGIDO)
            # =========================
            numero = "5532999781559"

            servico_nome = servico_escolhido.nome if servico_escolhido else "serviço"

            mensagem = f"""✨ Novo agendamento!

💄 Serviço: {servico_nome}
📅 Data: {data_str}
⏰ Hora: {hora_str}
👤 Cliente: {nome}
📱 WhatsApp: {telefone}

 """

            mensagem = quote(mensagem)

            whatsapp_url = f"https://api.whatsapp.com/send?phone={numero}&text={mensagem}"

            return redirect(whatsapp_url)

    return render_template(
        "agendar.html",
        servicos=servicos,
        horarios=horarios,
        erro=erro,
        hoje=hoje
    )

    # =========================
    # VERIFICAR BLOQUEIO
    # =========================
    bloqueado = False
    if data_obj:
        bloqueado = BloqueioData.query.filter_by(
            data=data_obj,
            ativo=True
        ).first() is not None

    return render_template(
        "agendar.html",
        servicos=servicos,
        horarios=horarios,
        erro=erro,
        hoje=hoje,
        bloqueado=bloqueado
    )
# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = Admin.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and check_password_hash(
                user.password,
                request.form["password"]
        ):
            login_user(user)
            return redirect(url_for("dashboard"))

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
@login_required
def dashboard():

    agendamentos = Agendamento.query.order_by(
        Agendamento.data,
        Agendamento.hora
    ).all()

    total_agendamentos = Agendamento.query.count()

    faturamento = db.session.query(
        func.sum(Financeiro.valor)
    ).filter(
        Financeiro.tipo == "Entrada"
    ).scalar() or 0

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    faturamento_mes = db.session.query(
        func.sum(Financeiro.valor)
    ).filter(
        Financeiro.tipo == "Entrada",
        extract("month", Financeiro.data) == mes_atual,
        extract("year", Financeiro.data) == ano_atual
    ).scalar() or 0

    total_produtos = Estoque.query.count()

    financeiros = Financeiro.query.order_by(Financeiro.data.desc()).all()
    estoque = Estoque.query.all()

    return render_template(
        "dashboard.html",
        agendamentos=agendamentos,
        total_agendamentos=total_agendamentos,
        faturamento=faturamento,
        faturamento_mes=faturamento_mes,
        total_produtos=total_produtos,
        financeiros=financeiros,
        estoque=estoque
    )


# =========================
# PAGINA BLOQUEIOS
# =========================
@app.route("/admin/bloqueios")
@login_required
def admin_bloqueios():
    bloqueios = BloqueioData.query.order_by(BloqueioData.data.desc()).all()
    return render_template(
        "admin_bloqueios.html",
        bloqueios=bloqueios
    )


# =========================
# HORÁRIOS ESPECIAIS
# =========================
@app.route("/admin/horarios-especiais")
@login_required
def horarios_especiais():

    horarios = HorarioEspecial.query.order_by(
        HorarioEspecial.data_inicio.desc()
    ).all()

    return render_template(
        "admin_horarios_especiais.html",
        horarios=horarios
    )


# =========================
# EXCLUIR HORÁRIO ESPECIAL
# =========================
@app.route("/admin/horarios-especiais/excluir/<int:id>")
@login_required
def excluir_horario_especial(id):

    horario = HorarioEspecial.query.get(id)

    if horario:
        db.session.delete(horario)
        db.session.commit()

    return redirect("/admin/horarios-especiais")


# =========================
# EXCLUIR BLOQUEIO
# =========================
@app.route("/admin/bloqueios/excluir/<int:id>")
@login_required
def excluir_bloqueio(id):

    bloqueio = BloqueioData.query.get(id)

    if bloqueio:
        db.session.delete(bloqueio)
        db.session.commit()

    return redirect("/admin/bloqueios")


## =========================
# SALVAR HORÁRIO ESPECIAL (CORRETO)
# =========================
@app.route("/admin/horarios-especiais/add", methods=["POST"])
@login_required
def add_horario_especial():

    inicio = request.form.get("inicio")
    fim = request.form.get("fim")
    hora_inicio = request.form.get("hora_inicio")
    hora_fim = request.form.get("hora_fim")
    dia_semana = request.form.get("dia_semana")

    novo = HorarioEspecial(
        data_inicio=datetime.strptime(inicio, "%Y-%m-%d").date(),
        data_fim=datetime.strptime(fim, "%Y-%m-%d").date(),
        dia_semana=int(dia_semana),
        inicio=hora_inicio,  # 🔥 STRING (CORRETO)
        fim=hora_fim,        # 🔥 STRING (CORRETO)
        ativo=True
    )

    db.session.add(novo)
    db.session.commit()

    return redirect("/admin/horarios-especiais")


# =========================
# SALVAR BLOQUEIO
# =========================
@app.route("/admin/bloqueios/add", methods=["POST"])
@login_required
def add_bloqueio():

    data = request.form.get("data")
    motivo = request.form.get("motivo")

    novo = BloqueioData(
        data=datetime.strptime(data, "%Y-%m-%d").date(),
        motivo=motivo
    )

    db.session.add(novo)
    db.session.commit()

    return redirect("/admin/bloqueios")


# =========================
# STATUS
# =========================
@app.route('/admin/agendamento/status/<int:id>/<status>')
@login_required
def mudar_status(id, status):

    agendamento = Agendamento.query.get(id)

    if agendamento:
        agendamento.status = status
        db.session.commit()

    return redirect(url_for('dashboard'))


# =========================
# EXCLUIR AGENDAMENTO
# =========================
@app.route('/admin/agendamento/excluir/<int:id>')
@login_required
def excluir_agendamento(id):

    agendamento = Agendamento.query.get(id)

    if agendamento:
        db.session.delete(agendamento)
        db.session.commit()

    return redirect(url_for('dashboard'))


# =========================
# PAINEL DE HORÁRIOS
# =========================
@app.route("/admin/horarios", methods=["GET", "POST"])
@login_required
def horarios_admin():

    if request.method == "POST":

        for h in HorarioFuncionamento.query.all():
            h.inicio = request.form.get(f"inicio_{h.id}")
            h.fim = request.form.get(f"fim_{h.id}")
            h.ativo = True if request.form.get(f"ativo_{h.id}") else False

        db.session.commit()
        return redirect("/admin/horarios")

    horarios = HorarioFuncionamento.query.order_by(
        HorarioFuncionamento.dia_semana
    ).all()

    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    return render_template(
        "horarios_admin.html",
        horarios=horarios,
        dias=dias
    )

# =========================
# PAINEL PRINCIPAL
# =========================
@app.route("/admin")
@login_required
def admin():
    try:
        # Retorna um template simples do painel principal
        return render_template("painel.html")
    except Exception as e:
        print("Erro ao abrir painel:", e)
        return "Erro ao abrir o painel", 500

# =========================
# FINANCEIRO
# =========================
@app.route("/admin/financeiro", methods=["GET", "POST"])
@login_required
def financeiro():
    if request.method == "POST":
        descricao = request.form.get("descricao")
        valor = request.form.get("valor")
        tipo = request.form.get("tipo")

        if descricao and valor and tipo:
            novo = Financeiro(
                descricao=descricao,
                valor=float(valor),
                tipo=tipo,
                data=datetime.now()
            )
            db.session.add(novo)
            db.session.commit()
            flash("Registro adicionado com sucesso!", "sucesso")
            return redirect(url_for("financeiro"))
        else:
            flash("Preencha todos os campos!", "erro")

    mes = request.args.get("mes")

    if mes:
        ano, mes_num = mes.split("-")
        registros = Financeiro.query.filter(
            extract("year", Financeiro.data) == int(ano),
            extract("month", Financeiro.data) == int(mes_num)
        ).order_by(Financeiro.data.desc()).all()
    else:
        registros = Financeiro.query.order_by(Financeiro.data.desc()).all()

    return render_template("financeiro_admin.html", registros=registros)

# =========================
# ADMIN ESTOQUE COMPLETO
# =========================
@app.route("/admin/estoque", methods=["GET", "POST"])
@login_required
def admin_estoque():

    if request.method == "POST":
        nome = request.form.get("nome")
        quantidade = request.form.get("quantidade")
        minimo = request.form.get("minimo")
        custo = request.form.get("custo")

        if nome and quantidade:
            novo = Estoque(
                nome=nome,
                quantidade=int(quantidade),
                minimo=int(minimo) if minimo else 0,
                custo=float(custo) if custo else 0.0
            )
            db.session.add(novo)
            db.session.commit()
            flash(f"Produto '{nome}' adicionado com sucesso!", "sucesso")
        else:
            flash("Preencha o nome e a quantidade do produto.", "erro")

        return redirect(url_for("admin_estoque"))

    estoque = Estoque.query.all()
    return render_template("estoque.html", produtos=estoque)


# =========================
# EXCLUIR ESTOQUE
# =========================
@app.route("/admin/estoque/excluir/<int:id>")
@login_required
def excluir_estoque(id):
    produto = Estoque.query.get_or_404(id)
    db.session.delete(produto)
    db.session.commit()
    flash(f"Produto '{produto.nome}' excluído com sucesso!", "sucesso")
    return redirect(url_for("admin_estoque"))


# =========================
# EDITAR ESTOQUE
# =========================
@app.route("/admin/estoque/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_estoque(id):
    produto = Estoque.query.get_or_404(id)

    if request.method == "POST":
        produto.nome = request.form.get("nome")
        produto.quantidade = int(request.form.get("quantidade"))
        produto.minimo = int(request.form.get("minimo")) if request.form.get("minimo") else 0
        produto.custo = float(request.form.get("custo")) if request.form.get("custo") else 0.0
        db.session.commit()
        flash(f"Produto '{produto.nome}' editado com sucesso!", "sucesso")
        return redirect(url_for("admin_estoque"))

    return render_template("editar_estoque.html", produto=produto)

# =========================
# EXCLUIR FINANCEIRO
# =========================
@app.route("/admin/financeiro/excluir/<int:id>")
@login_required
def excluir_financeiro(id):
    registro = Financeiro.query.get(id)

    if registro:
        db.session.delete(registro)
        db.session.commit()
        flash("Registro excluído com sucesso!", "sucesso")
    else:
        flash("Registro não encontrado!", "erro")

    return redirect(url_for("financeiro"))


# =========================
# EDITAR FINANCEIRO
# =========================
@app.route("/admin/financeiro/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_financeiro(id):
    registro = Financeiro.query.get(id)

    if not registro:
        flash("Registro não encontrado!", "erro")
        return redirect(url_for("financeiro"))

    if request.method == "POST":
        registro.descricao = request.form.get("descricao")
        registro.valor = float(request.form.get("valor"))
        registro.tipo = request.form.get("tipo")

        db.session.commit()
        flash("Registro editado com sucesso!", "sucesso")
        return redirect(url_for("financeiro"))

    return render_template("editar_financeiro.html", r=registro)
# =========================
# EDITAR Calendario 
# =========================

@app.route("/admin/agendamento/editar/<int:id>", methods=["POST"])
def editar_agendamento(id):
    from datetime import datetime
    a = Agendamento.query.get(id)

    data = request.json.get("data")
    hora = request.json.get("hora")

    a.data = datetime.strptime(data, "%Y-%m-%d")
    a.hora = hora

    db.session.commit()
    return {"status": "ok"}
@app.route("/admin/agendamento/confirmar/<int:id>")
def confirmar_agendamento(id):
    agendamento = Agendamento.query.get(id)
    agendamento.status = "Concluido"
    db.session.commit()
    return redirect("/dashboard")


# =========================
# FINAL
# =========================
if __name__ == "__main__":
    app.run(debug=True)
