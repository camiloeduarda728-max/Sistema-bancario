"""Sistema bancário em Python (POO)

Conceitos de POO usados:
- Abstração: Conta é uma classe abstrata (não pode ser instanciada).
- Herança: ContaCorrente e ContaPoupanca herdam de Conta.
- Polimorfismo: cada subclasse implementa sacar() do seu jeito.
- Encapsulamento: o saldo é "privado" e só muda por métodos.
- Composição: Cliente tem contas; Banco tem clientes e contas.
"""

from abc import ABC, abstractmethod
from datetime import datetime

# EXCEÇÕES
class BancoError(Exception):
    """Classe base de todos os erros do banco."""


class ValorInvalidoError(BancoError):
    """Valor zero, negativo ou não numérico."""


class SaldoInsuficienteError(BancoError):
    """Tentativa de sacar mais do que o disponível."""


class ContaNaoEncontradaError(BancoError):
    """Número de conta inexistente."""


class ClienteNaoEncontradoError(BancoError):
    """CPF não cadastrado."""


class ClienteJaExisteError(BancoError):
    """CPF já cadastrado."""

# CONTAS
class Conta(ABC):
    _proximo_numero = 1  # atributo de classe: compartilhado por todas as contas

    def __init__(self, titular):
        self.numero = Conta._proximo_numero
        Conta._proximo_numero += 1
        self.titular = titular      # objeto Cliente
        self._saldo = 0.0
        self._historico = []

    @property
    def saldo(self):
        """Permite ler conta.saldo, mas não alterar diretamente."""
        return self._saldo

    def depositar(self, valor):
        self._validar_valor(valor)
        self._saldo += valor
        self._registrar("Depósito", valor)

    @abstractmethod
    def sacar(self, valor):
        """Cada tipo de conta define suas próprias regras de saque."""

    def extrato(self):
        linhas = [f"--- Extrato da conta {self.numero} ({self.tipo()}) ---"]
        if not self._historico:
            linhas.append("Nenhuma movimentação.")
        for data, descricao, valor in self._historico:
            linhas.append(f"{data} | {descricao:<18} | R$ {valor:>10.2f}")
        linhas.append(f"Saldo atual: R$ {self._saldo:.2f}")
        return "\n".join(linhas)

    def tipo(self):
        return self.__class__.__name__

    @staticmethod
    def _validar_valor(valor):
        if not isinstance(valor, (int, float)) or valor <= 0:
            raise ValorInvalidoError("O valor deve ser um número maior que zero.")

    def _registrar(self, descricao, valor):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self._historico.append((agora, descricao, valor))

    def __str__(self):
        return (f"Conta {self.numero} | {self.tipo()} | "
                f"Titular: {self.titular.nome} | Saldo: R$ {self._saldo:.2f}")


class ContaCorrente(Conta):
    """Permite saldo negativo até o limite do cheque especial."""

    def __init__(self, titular, limite=500.0):
        super().__init__(titular)
        self.limite = limite

    def sacar(self, valor):
        self._validar_valor(valor)
        if valor > self._saldo + self.limite:
            raise SaldoInsuficienteError(
                f"Saldo + limite insuficiente. Disponível: "
                f"R$ {self._saldo + self.limite:.2f}"
            )
        self._saldo -= valor
        self._registrar("Saque", -valor)


class ContaPoupanca(Conta):
    """Não permite saldo negativo, mas rende juros."""

    def __init__(self, titular, taxa_rendimento=0.005):
        super().__init__(titular)
        self.taxa_rendimento = taxa_rendimento

    def sacar(self, valor):
        self._validar_valor(valor)
        if valor > self._saldo:
            raise SaldoInsuficienteError(
                f"Saldo insuficiente. Disponível: R$ {self._saldo:.2f}"
            )
        self._saldo -= valor
        self._registrar("Saque", -valor)

    def render_juros(self):
        """Aplica o rendimento mensal sobre o saldo."""
        juros = self._saldo * self.taxa_rendimento
        if juros > 0:
            self._saldo += juros
            self._registrar("Rendimento", juros)
        return juros



# CLIENTE
class Cliente:
    def __init__(self, nome, cpf):
        self.nome = nome
        self.cpf = cpf
        self.contas = []  # composição: um cliente TEM várias contas

    def adicionar_conta(self, conta):
        self.contas.append(conta)

    def __str__(self):
        return f"{self.nome} (CPF: {self.cpf}) - {len(self.contas)} conta(s)"

# BANCO
class Banco:
    def __init__(self, nome):
        self.nome = nome
        self._clientes = {}
        self._contas = {}

    def cadastrar_cliente(self, nome, cpf):
        if cpf in self._clientes:
            raise ClienteJaExisteError(f"CPF {cpf} já cadastrado.")
        cliente = Cliente(nome, cpf)
        self._clientes[cpf] = cliente
        return cliente

    def buscar_cliente(self, cpf):
        try:
            return self._clientes[cpf]
        except KeyError:
            raise ClienteNaoEncontradoError(f"CPF {cpf} não encontrado.")

    def abrir_conta(self, cpf, tipo):
        cliente = self.buscar_cliente(cpf)
        if tipo == "corrente":
            conta = ContaCorrente(cliente)
        elif tipo == "poupanca":
            conta = ContaPoupanca(cliente)
        else:
            raise ValueError("Tipo de conta inválido.")
        cliente.adicionar_conta(conta)
        self._contas[conta.numero] = conta
        return conta

    def buscar_conta(self, numero):
        try:
            return self._contas[numero]
        except KeyError:
            raise ContaNaoEncontradaError(f"Conta {numero} não encontrada.")

    def transferir(self, numero_origem, numero_destino, valor):
        if numero_origem == numero_destino:
            raise ValorInvalidoError("Origem e destino devem ser diferentes.")
        origem = self.buscar_conta(numero_origem)
        destino = self.buscar_conta(numero_destino)
        origem.sacar(valor)      # se falhar, lança exceção e nada é depositado
        destino.depositar(valor)

    def listar_contas(self):
        return list(self._contas.values())


# INTERFACE DE TERMINAL
MENU = """
========== BANCO X ==========
1 - Cadastrar cliente
2 - Abrir conta
3 - Depositar
4 - Sacar
5 - Transferir
6 - Ver extrato
7 - Listar contas
8 - Render juros (poupanças)
0 - Sair
=================================="""


def ler_float(mensagem):
    try:
        return float(input(mensagem).replace(",", "."))
    except ValueError:
        print("Digite um número válido.")
        return None


def ler_int(mensagem):
    try:
        return int(input(mensagem))
    except ValueError:
        print("Digite um número inteiro válido.")
        return None


def main():
    banco = Banco("Banco X")

    while True:
        print(MENU)
        opcao = input("Escolha uma opção: ").strip()

        try:
            if opcao == "1":
                nome = input("Nome: ").strip()
                cpf = input("CPF: ").strip()
                cliente = banco.cadastrar_cliente(nome, cpf)
                print(f"Cliente cadastrado: {cliente}")

            elif opcao == "2":
                cpf = input("CPF do cliente: ").strip()
                tipo = input("Tipo (corrente/poupanca): ").strip().lower()
                conta = banco.abrir_conta(cpf, tipo)
                print(f"Conta criada! Número: {conta.numero}")

            elif opcao == "3":
                numero = ler_int("Número da conta: ")
                valor = ler_float("Valor do depósito: R$ ")
                if numero is not None and valor is not None:
                    banco.buscar_conta(numero).depositar(valor)
                    print("Depósito realizado.")

            elif opcao == "4":
                numero = ler_int("Número da conta: ")
                valor = ler_float("Valor do saque: R$ ")
                if numero is not None and valor is not None:
                    banco.buscar_conta(numero).sacar(valor)
                    print("Saque realizado.")

            elif opcao == "5":
                origem = ler_int("Conta de origem: ")
                destino = ler_int("Conta de destino: ")
                valor = ler_float("Valor: R$ ")
                if None not in (origem, destino, valor):
                    banco.transferir(origem, destino, valor)
                    print("Transferência realizada.")

            elif opcao == "6":
                numero = ler_int("Número da conta: ")
                if numero is not None:
                    print(banco.buscar_conta(numero).extrato())

            elif opcao == "7":
                contas = banco.listar_contas()
                if not contas:
                    print("Nenhuma conta cadastrada.")
                for conta in contas:
                    print(conta)

            elif opcao == "8":
                for conta in banco.listar_contas():
                    if isinstance(conta, ContaPoupanca):
                        juros = conta.render_juros()
                        print(f"Conta {conta.numero}: +R$ {juros:.2f}")

            elif opcao == "0":
                print("Até logo!")
                break

            else:
                print("Opção inválida.")

        except (BancoError, ValueError) as erro:
            print(f"Erro: {erro}")


if __name__ == "__main__":
    main()