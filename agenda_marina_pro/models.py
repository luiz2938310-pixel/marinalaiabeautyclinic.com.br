from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# =========================
# ADMIN
# =========================
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# =========================
# SERVIÇOS
# =========================
class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    preco = db.Column(db.Float, nullable=False, default=0.0)
    duracao = db.Column(db.Integer, nullable=False)  # em minutos

    # relacionamento reverso
    agendamentos = db.relationship("Agendamento", backref="servico", lazy=True)


# =========================
# AGENDAMENTOS
# =========================

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    data = db.Column(db.Date)
    hora = db.Column(db.String(5))
    status = db.Column(db.String(20))
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'))


# =========================
# HORÁRIOS DE FUNCIONAMENTO (PADRÃO)
# =========================
class HorarioFuncionamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Segunda até 6=Domingo
    inicio = db.Column(db.String(5), nullable=False)    # "07:00"
    fim = db.Column(db.String(5), nullable=False)       # "20:00"
    ativo = db.Column(db.Boolean, default=True)


# =========================
# 🆕 BLOQUEIO DE DATAS (FERIADOS / FOLGAS)
# =========================
class BloqueioData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, unique=True)
    motivo = db.Column(db.String(200))
    ativo = db.Column(db.Boolean, default=True)


# =========================
# 🆕 HORÁRIO PERSONALIZADO POR PERÍODO
# =========================
class HorarioEspecial(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)

    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Seg até 6=Dom

    inicio = db.Column(db.String(5), nullable=False)  # "07:00"
    fim = db.Column(db.String(5), nullable=False)     # "14:00"

    ativo = db.Column(db.Boolean, default=True)


# =========================
# ESTOQUE
# =========================
class Estoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    minimo = db.Column(db.Integer, default=0)
    custo = db.Column(db.Float, default=0.0)


# =========================
# FINANCEIRO
# =========================
class Financeiro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # Entrada ou Saída
    valor = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200))
    data = db.Column(db.DateTime, default=datetime.utcnow)

# =========================
# Telefone
# =========================

