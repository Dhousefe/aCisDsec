@echo off
REM Este script eh executado pela aplicacao Python.
REM Sua saida eh redirecionada para um arquivo de log.

REM Cria o diretorio 'log' se ele nao existir dentro do diretorio atual.
REM O diretorio atual quando este script eh chamado pelo Python eh a pasta 'login'.
if not exist log mkdir log

REM -------------------------------------
REM Parametros padrao para o Login Server.
REM A saida agora sera redirecionada para a pasta 'log'
java -Xmx128m -cp ./libs/*; net.sf.l2j.loginserver.LoginServer > log\login_server.log 2>&1
REM -------------------------------------

REM O processo terminara aqui quando o comando 'java' for concluido ou encerrado.
