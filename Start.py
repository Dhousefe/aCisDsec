import tkinter as tk
from tkinter import scrolledtext, messagebox, font as tkFont, filedialog
import subprocess
import threading
import os
import time
import sys
import re # Para expressões regulares

# --- FUNÇÃO AUXILIAR PARA CAMINHOS DE RECURSOS (ÍCONE, ETC.) ---
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona em dev e no PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".") # Diretório do script em modo de desenvolvimento
    return os.path.join(base_path, relative_path)

# --- Classe para a Janela de Visualização de Log Individual (sem alterações) ---
class LogViewerWindow(tk.Toplevel):
    def __init__(self, master, log_file_path, server_name):
        super().__init__(master)
        self.title(f"Log do {server_name}")
        self.geometry("700x500")
        self.log_file_path = log_file_path
        self.server_name = server_name
        self.last_known_position = 0
        self.running = True

        bg_color = "#202020"
        fg_color = "white"
        try:
            self.log_font = tkFont.Font(family="Rokkit", size=10, weight="bold")
        except tk.TclError:
            self.log_font = tkFont.Font(family="Consolas", size=10, weight="bold")
            print("Aviso: Fonte 'Rokkit' não encontrada ou negrito indisponível. Usando 'Consolas' em negrito.")

        self.console_area = scrolledtext.ScrolledText(self, wrap=tk.WORD,
                                                      bg=bg_color, fg=fg_color,
                                                      font=self.log_font,
                                                      state=tk.DISABLED)
        self.console_area.pack(expand=True, fill="both", padx=5, pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.start_log_monitoring()

    def start_log_monitoring(self):
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    initial_content = f.read()
                    self.append_to_console(initial_content)
                    self.last_known_position = f.tell()
            except Exception as e:
                self.append_to_console(f"Erro ao carregar log antigo de {self.server_name}: {e}\n")
        else:
            self.append_to_console(f"[{self.server_name}] Arquivo de log não encontrado. Aguardando a criação...\n")

        self.monitor_thread = threading.Thread(target=self._monitor_log_file, daemon=True)
        self.monitor_thread.start()

    def _monitor_log_file(self):
        while self.running:
            try:
                if not os.path.exists(self.log_file_path):
                    time.sleep(1)
                    continue

                current_size = os.path.getsize(self.log_file_path)

                if current_size < self.last_known_position:
                    self.append_to_console(f"\n--- [{self.server_name}] Arquivo de log resetado ou reiniciado. Recarregando... ---\n")
                    self.last_known_position = 0
                    # Clear existing content and then append reloaded
                    self.after(0, lambda: self._do_clear_and_append("")) # Clear first
                    with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        reloaded_content = f.read()
                        self.append_to_console(reloaded_content) # Append after clear
                        self.last_known_position = f.tell()
                
                elif current_size > self.last_known_position:
                    with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self.last_known_position)
                        new_content = f.read()
                        self.append_to_console(new_content)
                        self.last_known_position = f.tell()

            except Exception as e:
                # Avoid flooding with identical errors if file temporarily inaccessible
                error_msg = f"Erro ao monitorar arquivo de log de {self.server_name}: {e}\n"
                # Basic check to prevent identical consecutive messages, could be more sophisticated
                current_text = self.console_area.get("end-2l linestart", "end-1c") # Get previous line
                if error_msg.strip() not in current_text:
                    self.append_to_console(error_msg)
            finally:
                time.sleep(0.5)

    def append_to_console(self, text):
        self.after(0, lambda: self._do_append(text))

    def _do_append(self, text):
        if not self.console_area.winfo_exists(): return # Avoid error if window closed
        self.console_area.config(state=tk.NORMAL)
        self.console_area.insert(tk.END, text)
        self.console_area.see(tk.END)
        self.console_area.config(state=tk.DISABLED)

    def _do_clear_and_append(self, text):
        if not self.console_area.winfo_exists(): return
        self.console_area.config(state=tk.NORMAL)
        self.console_area.delete(1.0, tk.END)
        if text: # Only insert if text is provided (might be empty if just clearing)
            self.console_area.insert(tk.END, text)
            self.console_area.see(tk.END)
        self.console_area.config(state=tk.DISABLED)

    def on_closing(self):
        self.running = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1) # Give a bit of time for thread to close
        self.destroy()

# --- Classe para a Janela de Edição de Configuração (sem alterações) ---
class ConfigEditorWindow(tk.Toplevel):
    def __init__(self, master, config_file_path, server_name, manager_instance):
        super().__init__(master)
        self.title(f"Editar Configuração: {server_name}")
        self.geometry("800x800")
        self.config_file_path = config_file_path
        self.server_name = server_name
        self.manager_instance = manager_instance # To call append_to_manager_console

        bg_color_editor = "#303030"
        fg_color_editor = "cyan"
        try:
            self.editor_font = tkFont.Font(family="Consolas", size=11)
        except tk.TclError:
            self.editor_font = tkFont.Font(family="monospace", size=11) # Fallback

        self.editor_area = scrolledtext.ScrolledText(self, wrap=tk.WORD,
                                                      bg=bg_color_editor, fg=fg_color_editor,
                                                      font=self.editor_font,
                                                      insertbackground="white") # Cursor color
        self.editor_area.pack(expand=True, fill="both", padx=5, pady=5)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        save_button = tk.Button(button_frame, text="Salvar Alterações", command=self.save_config)
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = tk.Button(button_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)

        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor_area.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo de configuração:\n{self.config_file_path}\nErro: {e}")
                self.manager_instance.append_to_manager_console(f"Erro ao ler {self.config_file_path}: {e}\n")
                self.destroy() # Close editor if file can't be read
        else:
            messagebox.showerror("Arquivo Não Encontrado", f"O arquivo de configuração não existe:\n{self.config_file_path}")
            self.manager_instance.append_to_manager_console(f"Arquivo de config não encontrado: {self.config_file_path}\n")
            self.destroy() # Close editor if file doesn't exist

    def save_config(self):
        try:
            content = self.editor_area.get(1.0, tk.END)
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("Sucesso", f"Configuração de {self.server_name} salva com sucesso!\nPara aplicar as alterações, por favor, reinicie os servidores.")
            self.manager_instance.append_to_manager_console(f"Configuração de {self.server_name} salva em {self.config_file_path}\n")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro de Salvamento", f"Não foi possível salvar o arquivo de configuração:\n{self.config_file_path}\nErro: {e}")
            self.manager_instance.append_to_manager_console(f"Erro ao salvar {self.config_file_path}: {e}\n")


# --- Classe Principal do Gerenciador de Servidores ---
class GameServerManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Servidores aCis409 By Dhousefe")
        
        # --- DEFINIR ÍCONE DA JANELA ---
        try:
            # Supondo que 'app_icon.ico' está no mesmo diretório que o script
            # ou incluído corretamente se você usar PyInstaller
            icon_path = resource_path("app_icon.ico") 
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                # Para outros sistemas operacionais ou ícones .png/.gif, você pode tentar:
                # img = tk.PhotoImage(file=resource_path('app_icon.png'))
                # self.tk.call('wm', 'iconphoto', self._w, img)
            else:
                # A console do gerenciador ainda não está pronta aqui, então usamos print
                print("AVISO: Ícone 'app_icon.ico' não encontrado.")
        except Exception as e:
            print(f"AVISO: Erro ao definir o ícone da aplicação: {e}")
        # --- FIM DA DEFINIÇÃO DO ÍCONE ---
            
        self.geometry("1024x750")

        self.login_server_process = None
        self.game_server_process = None

        # Determinar o diretório base do script
        if getattr(sys, 'frozen', False):
            # Se rodando como um executável PyInstaller
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Se rodando como um script .py normal
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.login_bat_path = os.path.join(self.base_dir, "aCis_datapack", "build", "login", "startLoginServer.bat")
        self.game_bat_path = os.path.join(self.base_dir, "aCis_datapack", "build", "gameserver", "startGameServer.bat")

        self.game_log_path = os.path.join(self.base_dir, "aCis_datapack", "build", "gameserver", "log", "game_server.log") # NOVO CAMINHO CORRETO

        self.login_log_path = os.path.join(self.base_dir, "aCis_datapack", "build", "login", "log", "login_server.log") # NOVO CAMINHO CORRETO

        # Se seus logs têm nomes diferentes ou estão em outros locais, ajuste aqui.
        # self.login_log_path = os.path.join(self.base_dir, "login", "login_server.log") # Original
        # self.game_log_path = os.path.join(self.base_dir, "gameserver", "game_server.log") # Original


        self.login_config_path = os.path.join(self.base_dir, "aCis_datapack", "build", "login", "config", "loginserver.properties")
        self.game_config_path = os.path.join(self.base_dir, "aCis_datapack", "build", "gameserver", "config", "server.properties")
        
        self.log_viewer_windows = {}
        self.config_editor_windows = {}

        self.ports_to_check = [7777, 9014, 2106] # Portas comuns L2J

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    # Método dentro da classe GameServerManager
    def _compare_versions(self, version_str1, version_str2):
        """
        Compara duas strings de versão (ex: "10.5.28", "10.11.2").
        Retorna:
         1 se version_str1 > version_str2
        -1 se version_str1 < version_str2
         0 se version_str1 == version_str2
        """
        v1_parts = []
        v2_parts = []
        try:
            v1_parts = list(map(int, version_str1.split('.')))
            v2_parts = list(map(int, version_str2.split('.')))
        except ValueError:
            # MENSAGEM EM PT-BR
            self.append_to_manager_console(f"Erro ao converter componentes da versão para número: '{version_str1}' vs '{version_str2}'.\n")
            return -1 

        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            if p1 < p2: return -1
            if p1 > p2: return 1
        return 0

    def _check_mariadb_status_and_version(self, service_name="MariaDB", required_version_str="10.5.28"):
        """
        Verifica o status do serviço MariaDB, sua versão e se é igual ou superior à requerida.
        (Apenas Windows)
        Retorna: (bool_status, str_mensagem_ou_versao)
        """
        if sys.platform != "win32":
            self.append_to_manager_console("A verificação de versão e status do MariaDB é suportada apenas no Windows.\n")
            return False, "Não é Windows" # MENSAGEM DE RETORNO PT-BR

        self.append_to_manager_console(f"Verificando serviço '{service_name}' e versão (requerida: {required_version_str} ou superior)...\n")

        binary_path = None
        is_running = False

        try:
            sc_qc_command = ["sc", "qc", service_name]
            qc_process = subprocess.run(
                sc_qc_command, capture_output=True, text=True, errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if qc_process.returncode == 0:
                match = re.search(r"BINARY_PATH_NAME\s+:\s+(.+)", qc_process.stdout, re.IGNORECASE)
                if match:
                    binary_path = match.group(1).strip().strip('"')
                    if " " in binary_path and not (binary_path.startswith('"') and binary_path.endswith('"')):
                         binary_path = f'"{binary_path}"'
                    self.append_to_manager_console(f"Caminho do binário para '{service_name}': {binary_path}\n")
                else:
                    self.append_to_manager_console(f"Não foi possível encontrar BINARY_PATH_NAME para o serviço '{service_name}'.\n")
            else:
                if "1060" in qc_process.stderr or "1060" in qc_process.stdout: # Código de erro para serviço não existente
                    self.append_to_manager_console(f"Serviço '{service_name}' não encontrado (Código 1060).\n")
                    return False, "Serviço Não Encontrado" # MENSAGEM DE RETORNO PT-BR
                self.append_to_manager_console(f"Erro ao executar 'sc qc {service_name}': {qc_process.stderr or qc_process.stdout}\n")
                return False, "Erro ao Consultar Serviço" # MENSAGEM DE RETORNO PT-BR

            sc_query_command = ["sc", "query", service_name]
            query_process = subprocess.run(
                sc_query_command, capture_output=True, text=True, errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if "RUNNING" in query_process.stdout:
                is_running = True
                self.append_to_manager_console(f"Serviço '{service_name}' está RODANDO.\n")
            else:
                self.append_to_manager_console(f"Serviço '{service_name}' NÃO está rodando.\n")
                return False, "Serviço Não Rodando" # MENSAGEM DE RETORNO PT-BR

        except FileNotFoundError:
            self.append_to_manager_console("Erro: Comando 'sc' (Service Control) não encontrado.\n")
            return False, "Erro Comando SC" # MENSAGEM DE RETORNO PT-BR
        except Exception as e:
            self.append_to_manager_console(f"Erro ao verificar status/caminho do serviço '{service_name}': {e}\n")
            return False, f"Erro no Serviço ({e})" # MENSAGEM DE RETORNO PT-BR

        if is_running and binary_path:
            try:
                version_command = f"{binary_path} --version"
                version_process = subprocess.run(
                    version_command, shell=True,
                    capture_output=True, text=True, errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if version_process.returncode == 0 and version_process.stdout:
                    version_match = re.search(r"Ver\s+(\d+\.\d+\.\d+)", version_process.stdout, re.IGNORECASE)
                    if version_match:
                        detected_version_str = version_match.group(1)
                        self.append_to_manager_console(f"Versão detectada do MariaDB: {detected_version_str}\n")
                        
                        comparison_result = self._compare_versions(detected_version_str, required_version_str)
                        if comparison_result >= 0:
                            self.append_to_manager_console(f"Versão do MariaDB ({detected_version_str}) é adequada (igual ou superior a {required_version_str}).\n")
                            return True, detected_version_str # Retorna versão detectada para exibição
                        else:
                            self.append_to_manager_console(f"Versão do MariaDB ({detected_version_str}) é INFERIOR à requerida ({required_version_str}).\n")
                            return False, f"Versão Baixa ({detected_version_str})" # MENSAGEM DE RETORNO PT-BR
                    else:
                        self.append_to_manager_console(f"Não foi possível extrair o número da versão da saída de '{version_command}':\n{version_process.stdout.strip()}\n")
                        return False, "Erro ao Extrair Versão" # MENSAGEM DE RETORNO PT-BR
                else:
                    self.append_to_manager_console(f"Comando '{version_command}' falhou ou não retornou saída.\nCódigo de retorno: {version_process.returncode}\nSaída padrão: {version_process.stdout.strip()}\nSaída de erro: {version_process.stderr.strip()}\n")
                    return False, "Erro ao Executar --version" # MENSAGEM DE RETORNO PT-BR
            except Exception as e:
                self.append_to_manager_console(f"Erro ao obter/verificar versão do MariaDB: {e}\n")
                return False, f"Erro na Verificação da Versão ({e})" # MENSAGEM DE RETORNO PT-BR
        
        return False, "Status Desconhecido" # MENSAGEM DE RETORNO PT-BR    

    def create_widgets(self):
        # Frame principal superior para botões de controle e edição
        top_controls_frame = tk.Frame(self)
        top_controls_frame.pack(fill="x", padx=10, pady=5)

        # Frame para botões de edição de configuração (canto superior esquerdo)
        config_edit_frame = tk.LabelFrame(top_controls_frame, text="Editar Configurações", padx=5, pady=5)
        config_edit_frame.pack(side=tk.LEFT, padx=10, pady=5, anchor='nw') # Anchor to North-West

        self.edit_login_config_button = tk.Button(config_edit_frame, text="Login Config",
                                                  command=lambda: self.open_config_editor(self.login_config_path, "LoginServer"),
                                                  font=("Arial", 9))
        self.edit_login_config_button.pack(side=tk.LEFT, padx=5)

        self.edit_game_config_button = tk.Button(config_edit_frame, text="Game Config",
                                                 command=lambda: self.open_config_editor(self.game_config_path, "GameServer"),
                                                 font=("Arial", 9))
        self.edit_game_config_button.pack(side=tk.LEFT, padx=5)

        # Frame para botões de controle de servidor (centro)
        server_control_frame = tk.LabelFrame(top_controls_frame, text="Controle de Servidores", padx=10, pady=10)
        # Pack server_control_frame to fill available space or center it better
        server_control_frame.pack(side=tk.LEFT, padx=20, pady=5, expand=True)


        self.start_all_button = tk.Button(server_control_frame, text="Iniciar Servidores",
                                          command=self.start_all_servers,
                                          font=("Arial", 12, "bold"), bg="green", fg="white",
                                          width=18, height=2)
        self.start_all_button.pack(side=tk.LEFT, padx=10)

        self.stop_all_button = tk.Button(server_control_frame, text="Parar Servidores",
                                         command=self.stop_all_servers,
                                         font=("Arial", 12, "bold"), bg="red", fg="white",
                                         width=18, height=2, state=tk.DISABLED)
        self.stop_all_button.pack(side=tk.LEFT, padx=10)

        # Frame para botões de visualização de logs (direita)
        log_viewer_frame = tk.LabelFrame(top_controls_frame, text="Visualização de Logs", padx=10, pady=10)
        log_viewer_frame.pack(side=tk.RIGHT, padx=10, pady=5, anchor='ne') # Anchor to North-East

        self.view_login_log_button = tk.Button(log_viewer_frame, text="Ver Log Login",
                                               command=lambda: self.open_log_viewer(self.login_log_path, "LoginServer"),
                                               font=("Arial", 10), width=15)
        self.view_login_log_button.pack(side=tk.LEFT, padx=5)

        self.view_game_log_button = tk.Button(log_viewer_frame, text="Ver Log Game",
                                              command=lambda: self.open_log_viewer(self.game_log_path, "GameServer"),
                                              font=("Arial", 10), width=15)
        self.view_game_log_button.pack(side=tk.LEFT, padx=5)
        
        
        
        # --- Seção: Ações do Projeto (Dependências e Compilação) ---
        # Podemos renomear o LabelFrame para refletir as novas ações
        project_actions_frame = tk.LabelFrame(self, text="Ações do Projeto", padx=10, pady=10)
        project_actions_frame.pack(fill="x", padx=10, pady=5)

        # Sub-frame para alinhar os botões de ação horizontalmente
        action_buttons_subframe = tk.Frame(project_actions_frame)
        action_buttons_subframe.pack(pady=5) # Centraliza o grupo de botões

        # Botão Verificar Dependências (existente)
        self.check_deps_button = tk.Button(action_buttons_subframe, text="Verificar Dependências",
                                           command=self.check_all_dependencies,
                                           font=("Arial", 10, "bold"), bg="orange", fg="white")
        self.check_deps_button.pack(side=tk.LEFT, padx=10) # padx para espaçamento

        # NOVO BOTÃO: Compilar projeto (git)
        self.compile_project_button = tk.Button(action_buttons_subframe, text="Compilar projeto (git)",
                                                command=self.compile_project_git, # Novo método de comando
                                                font=("Arial", 10, "bold"), bg="dodgerblue", fg="white") # Estilo de exemplo
        self.compile_project_button.pack(side=tk.LEFT, padx=10)
        
        # Labels para mostrar o status das dependências (permanecem em project_actions_frame)
        self.java_status_label = tk.Label(project_actions_frame, text="Java (OpenJDK-21): Não Verificado", fg="gray")
        self.java_status_label.pack(anchor="w", padx=10)
        
        self.mariadb_status_label = tk.Label(project_actions_frame, text="BD (MariaDB/MySQL 10.5.28+): Não Verificado", fg="gray")
        self.mariadb_status_label.pack(anchor="w", padx=10)
        
        self.mariadb_default_path_label = tk.Label(project_actions_frame, text="Caminho Padrão MariaDB 10.5: Não Verificado", fg="gray")
        self.mariadb_default_path_label.pack(anchor="w", padx=10)
        
        # Botões de download (são declarados aqui, mas sua exibição é controlada em check_all_dependencies)
        self.java_download_button = tk.Button(project_actions_frame, text="Baixar OpenJDK-21", 
                                              command=self.download_openjdk, state=tk.DISABLED)
        # Nota: .pack() para os botões de download é chamado dentro de check_all_dependencies quando necessário.
        
        self.mariadb_download_button = tk.Button(project_actions_frame, text="Baixar MariaDB", 
                                                 command=self.download_mariadb, state=tk.DISABLED)



        # Área de texto para mensagens do gerenciador
        self.manager_console_area = scrolledtext.ScrolledText(self, wrap=tk.WORD,
                                                              bg="gray20", fg="white",
                                                              font=("Consolas", 10),
                                                              state=tk.DISABLED)
        self.manager_console_area.pack(expand=True, fill="both", padx=10, pady=10)
        self.append_to_manager_console("Console do Gerenciador de Servidores aCis\n")
        self.append_to_manager_console(f"Diretório base: {self.base_dir}\n")
        self.append_to_manager_console(f"Login BAT: {self.login_bat_path}\n")
        self.append_to_manager_console(f"Game BAT: {self.game_bat_path}\n")
        
    def compile_project_git(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.append_to_manager_console(f"[{timestamp}] Comando 'Compilar projeto (git)' acionado.\n")
        
        # Desabilitar o botão para evitar múltiplos cliques durante a execução
        self.compile_project_button.config(state=tk.DISABLED)
        
        # Iniciar a compilação em uma nova thread para não bloquear a GUI
        compilation_thread = threading.Thread(target=self._perform_compilation_thread, daemon=True)
        compilation_thread.start()
        
        
    def append_to_manager_console_from_thread(self, text):
        """ Envia texto para a console do gerenciador de forma segura a partir de uma thread. """
        self.after(0, lambda: self.append_to_manager_console(text))
        
    def _run_command_and_stream_output(self, command_list, working_directory, custom_env=None): # Adicionado custom_env
        """
        Executa um comando externo e transmite seu stdout/stderr para a console do gerenciador.
        Aceita um dicionário 'custom_env' para variáveis de ambiente adicionais/substituídas.
        Retorna True se o comando for bem-sucedido (código de saída 0), False caso contrário.
        """
        try:
            process_encoding = 'oem' if sys.platform == "win32" else 'utf-8'
            self.append_to_manager_console_from_thread(f"Executando: {' '.join(command_list)} em '{working_directory}'\n")
            
            # Prepara o ambiente para o subprocesso
            effective_env = os.environ.copy()  # Começa com uma cópia do ambiente atual
            if custom_env:
                effective_env.update(custom_env) # Adiciona ou sobrescreve com as variáveis customizadas

            process = subprocess.Popen(
                command_list,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=process_encoding,
                errors='replace',
                bufsize=1,
                universal_newlines=True,
                env=effective_env,  # Usa o ambiente preparado
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            if process.stdout:
                for line in process.stdout:
                    self.append_to_manager_console_from_thread(line)
            
            process.wait()
            
            if process.returncode == 0:
                self.append_to_manager_console_from_thread(f"Comando '{command_list[0]}' finalizado com sucesso.\n")
                return True
            else:
                self.append_to_manager_console_from_thread(f"ERRO: Comando '{command_list[0]}' falhou com código de saída {process.returncode}.\n")
                return False

        except FileNotFoundError:
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO: Executável '{command_list[0]}' não encontrado. Verifique o caminho.\n")
            return False
        except Exception as e:
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO ao executar '{' '.join(command_list)}': {e}\n")
            return False
            

    def _perform_compilation_thread(self):
        # !!! IMPORTANTE: CONFIGURE ESTE CAMINHO PARA O CÓDIGO FONTE DO PROJETO !!!
        project_source_dir = os.path.join(self.base_dir, "aCisDsec_project") 
        # Ex: r"E:\aCisDsec\pasta\aCisDsec_source" ou onde quer que o código do aCisDsec deva ficar.

        git_repo_url = "https://github.com/Dhousefe/aCisDsec.git"
        git_branch = "master" 

        self.append_to_manager_console_from_thread(f"\n--- Iniciando processo de compilação do projeto ---\n")
        self.append_to_manager_console_from_thread(f"Diretório do projeto alvo: {project_source_dir}\n")
        self.append_to_manager_console_from_thread(f"Repositório Git: {git_repo_url}, Branch: {git_branch}\n")

        # --- ETAPA 1: OPERAÇÕES GIT (CLONE OU PULL) ---
        # (Esta parte permanece como na resposta anterior - verifica Git, clona ou faz pull)
        # ... (código da Etapa 1 - Git aqui) ...
        # Certifique-se que, se esta etapa falhar, o método retorne e chame _compilation_finished(False, ...)
        self.append_to_manager_console_from_thread(f"\n--- Etapa 1: Verificando e atualizando código fonte via Git ---\n")
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.append_to_manager_console_from_thread("ERRO: Comando 'git' não encontrado. Verifique se o Git está instalado e no PATH do sistema.\n")
            self.after(0, lambda: self._compilation_finished(False, "Git não encontrado."))
            return

        git_repo_path_dot_git = os.path.join(project_source_dir, ".git")
        perform_pull_after_setup = False

        if os.path.isdir(project_source_dir):
            if os.path.isdir(git_repo_path_dot_git):
                self.append_to_manager_console_from_thread(f"Diretório do projeto '{project_source_dir}' encontrado e é um repositório Git.\n")
                perform_pull_after_setup = True
            else:
                self.append_to_manager_console_from_thread(
                    f"ERRO: O diretório '{project_source_dir}' existe, mas não é um repositório Git válido (pasta .git não encontrada).\n"
                    f"Por favor, remova ou mova este diretório, ou certifique-se de que é um clone válido.\n"
                )
                self.after(0, lambda: self._compilation_finished(False, "Diretório do projeto inválido (não é repositório Git)."))
                return
        else:
            self.append_to_manager_console_from_thread(f"Diretório do projeto '{project_source_dir}' não encontrado. Tentando clonar o repositório...\n")
            parent_dir = os.path.dirname(project_source_dir)
            clone_target_folder_name = os.path.basename(project_source_dir)
            if not os.path.isdir(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    self.append_to_manager_console_from_thread(f"Diretório pai '{parent_dir}' criado/verificado.\n")
                except Exception as e:
                    self.append_to_manager_console_from_thread(f"ERRO: Falha ao criar diretório pai '{parent_dir}': {e}\n")
                    self.after(0, lambda: self._compilation_finished(False, "Falha ao criar diretório pai."))
                    return
            
            git_clone_command = ["git", "clone", "--branch", git_branch, git_repo_url, clone_target_folder_name]
            self.append_to_manager_console_from_thread(f"Executando clone em '{parent_dir}' para a pasta '{clone_target_folder_name}'...\n")
            clone_success = self._run_command_and_stream_output(git_clone_command, parent_dir) 
            if not clone_success:
                self.append_to_manager_console_from_thread(f"ERRO: Falha ao clonar o repositório '{git_repo_url}'. Verifique as mensagens.\n")
                self.after(0, lambda: self._compilation_finished(False, "Falha ao clonar repositório."))
                return
            self.append_to_manager_console_from_thread("Repositório clonado com sucesso.\n")
            perform_pull_after_setup = True 

        if perform_pull_after_setup:
            self.append_to_manager_console_from_thread(f"Garantindo o branch '{git_branch}' e atualizando via 'git pull' em '{project_source_dir}'...\n")
            checkout_command = ["git", "checkout", git_branch]
            self._run_command_and_stream_output(checkout_command, project_source_dir) 

            pull_command = ["git", "pull", "origin", git_branch]
            pull_success = self._run_command_and_stream_output(pull_command, project_source_dir)
            if not pull_success:
                self.append_to_manager_console_from_thread("ERRO: Falha ao executar 'git pull'. Verifique as mensagens (possíveis conflitos ou problemas de conexão).\n")
                self.after(0, lambda: self._compilation_finished(False, "Falha no git pull."))
                return
            self.append_to_manager_console_from_thread("'git pull' concluído com sucesso.\n")
        
        self.append_to_manager_console_from_thread(f"--- Etapa 1: Código fonte do projeto '{os.path.basename(project_source_dir)}' pronto. ---\n")


        # --- ETAPA 2: CONFIGURAÇÃO E VERIFICAÇÃO DO ANT (DENTRO DO PROJETO GIT) ---
        self.append_to_manager_console_from_thread(f"\n--- Etapa 2: Configurando e verificando Ant (embutido no projeto Git) ---\n")
        
        ant_folder_name_in_project = "Ant"  # Nome da pasta "Ant" DENTRO do seu aCisDsec_project
        # *** CORREÇÃO PRINCIPAL AQUI: ant_home_path é relativo a project_source_dir ***
        ant_home_path = os.path.join(project_source_dir, ant_folder_name_in_project) 
        
        ant_bin_path = os.path.join(ant_home_path, "bin")
        ant_executable_name = "ant.bat" if sys.platform == "win32" else "ant"
        ant_executable_full_path = os.path.join(ant_bin_path, ant_executable_name)

        self.append_to_manager_console_from_thread(f"Procurando Ant do projeto em: {ant_home_path}\n")

        if not os.path.isdir(ant_home_path) or not os.path.isfile(ant_executable_full_path):
            self.append_to_manager_console_from_thread(
                f"ERRO: Pasta Ant do projeto ('{ant_home_path}') ou executável ('{ant_executable_full_path}') não encontrado DENTRO de '{project_source_dir}'.\n"
                f"Verifique se o repositório Git '{os.path.basename(project_source_dir)}' contém uma pasta '{ant_folder_name_in_project}' com uma instalação válida do Ant (incluindo 'bin/{ant_executable_name}').\n"
                f"Se a pasta 'Ant' não faz parte do repositório Git, ela deveria estar ao lado do 'Start.py' e o caminho para 'ant_home_path' deveria ser 'os.path.join(self.base_dir, \"{ant_folder_name_in_project}\")'.\n"
            )
            self.after(0, lambda: self._compilation_finished(False, f"Ant não encontrado dentro do projeto em '{ant_folder_name_in_project}'."))
            return

        # O restante da configuração do ambiente Ant e execução permanece o mesmo
        ant_env = os.environ.copy()
        ant_env["ANT_HOME"] = ant_home_path
        ant_env["PATH"] = ant_bin_path + os.pathsep + ant_env.get("PATH", "")
        # Potencialmente adicionar JAVA_HOME ao ant_env aqui, se necessário e detectado
        
        self.append_to_manager_console_from_thread(f"Verificando Ant do projeto com '{ant_executable_full_path} -version'...\n")
        try:
            result = subprocess.run(
                [ant_executable_full_path, "-version"], capture_output=True, check=True, text=True,
                env=ant_env, encoding='oem' if sys.platform == "win32" else 'utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            first_line_version = result.stdout.splitlines()[0] if result.stdout.splitlines() else "Não foi possível obter a versão."
            self.append_to_manager_console_from_thread(f"INFO: Ant do projeto funcional. ({first_line_version})\n")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.append_to_manager_console_from_thread(
                f"ERRO: Falha ao executar o Ant do projeto ('{ant_executable_full_path} -version').\n"
                f"Causa: {e}\n"
                f"Verifique a pasta '{ant_folder_name_in_project}' dentro de '{project_source_dir}' e se o Java (JDK) está corretamente configurado e acessível.\n"
            )
            self.after(0, lambda: self._compilation_finished(False, "Falha ao verificar Ant do projeto."))
            return
        self.append_to_manager_console_from_thread(f"--- Etapa 2: Ant do projeto pronto. ---\n")

        # --- ETAPA 3: COMPILAÇÃO COM ANT EMBUTIDO NO PROJETO ---
        # (Esta parte permanece como na resposta anterior, usando ant_executable_full_path, project_source_dir e ant_env)
        # ... (código da Etapa 3 - Compilação com Ant aqui) ...
        # --- ETAPA 3: COMPILAÇÃO COM ANT EMBUTIDO NO PROJETO (DATAPACK E GAMESERVER) ---
        self.append_to_manager_console_from_thread(f"\n--- Etapa 3: Compilando o projeto '{os.path.basename(project_source_dir)}' com Ant do projeto ---\n")
        
        # Definir os nomes dos diretórios e targets do Ant (ajuste os targets se necessário)
        datapack_module_name = "aCis_datapack"
        gameserver_module_name = "aCis_gameserver"
        
        ant_target_default = "dist" # Target comum, pode ser "" para o target padrão do build.xml

        # --- 3.1 Compilação do Datapack ---
        datapack_build_dir = os.path.join(project_source_dir, datapack_module_name)
        datapack_build_file = os.path.join(datapack_build_dir, "build.xml")
        datapack_compile_success = False # Inicializa como falha

        self.append_to_manager_console_from_thread(f"\n3.1. Compilando Datapack em: '{datapack_build_dir}'...\n")

        if not os.path.isfile(datapack_build_file):
            self.append_to_manager_console_from_thread(f"ERRO: Arquivo 'build.xml' não encontrado para o Datapack em '{datapack_build_dir}'. Pulando compilação do Datapack.\n")
        else:
            ant_compile_command_datapack = [ant_executable_full_path]
            # Use um target específico para o datapack se houver, senão o default.
            # Ex: ant_target_datapack = "build_datapack" ou deixe ant_target_default
            if ant_target_default: 
                ant_compile_command_datapack.append(ant_target_default) 
            
            datapack_compile_success = self._run_command_and_stream_output(
                ant_compile_command_datapack, 
                datapack_build_dir,  # Define o diretório de trabalho para a pasta do datapack
                custom_env=ant_env
            )

            if not datapack_compile_success:
                self.append_to_manager_console_from_thread(f"ERRO: Falha ao compilar o Datapack. Verifique as mensagens acima.\n")
            else:
                self.append_to_manager_console_from_thread(f"Compilação do Datapack concluída {'com sucesso' if datapack_compile_success else 'com falha'}.\n")

        # --- 3.2 Compilação do GameServer ---
        gameserver_build_dir = os.path.join(project_source_dir, gameserver_module_name)
        gameserver_build_file = os.path.join(gameserver_build_dir, "build.xml")
        gameserver_compile_success = False # Inicializa como falha

        self.append_to_manager_console_from_thread(f"\n3.2. Compilando GameServer em: '{gameserver_build_dir}'...\n")

        if not os.path.isfile(gameserver_build_file):
            self.append_to_manager_console_from_thread(f"ERRO: Arquivo 'build.xml' não encontrado para o GameServer em '{gameserver_build_dir}'. Pulando compilação do GameServer.\n")
        else:
            ant_compile_command_gameserver = [ant_executable_full_path]
            # Use um target específico para o gameserver se houver, senão o default.
            # Ex: ant_target_gameserver = "build_gameserver" ou deixe ant_target_default
            if ant_target_default:
                ant_compile_command_gameserver.append(ant_target_default)

            gameserver_compile_success = self._run_command_and_stream_output(
                ant_compile_command_gameserver, 
                gameserver_build_dir, # Define o diretório de trabalho para a pasta do gameserver
                custom_env=ant_env
            )

            if not gameserver_compile_success:
                self.append_to_manager_console_from_thread(f"ERRO: Falha ao compilar o GameServer. Verifique as mensagens acima.\n")
            else:
                self.append_to_manager_console_from_thread(f"Compilação do GameServer concluída {'com sucesso' if gameserver_compile_success else 'com falha'}.\n")

        # --- Finalização da Compilação ---
        # Considera sucesso geral se AMBOS compilarem com sucesso.
        # Ajuste esta lógica se, por exemplo, o datapack for opcional ou se você quiser
        # que a falha de um não impeça o sucesso do outro em termos de mensagem final.
        overall_success = datapack_compile_success and gameserver_compile_success
        
        if overall_success:
            self.append_to_manager_console_from_thread("\n--- Compilação do projeto (Datapack e GameServer) finalizada com sucesso! ---\n")
            self.after(0, lambda: self._compilation_finished(True, "Compilação do Datapack e GameServer finalizada com sucesso!"))
        else:
            error_parts = []
            if not datapack_compile_success: error_parts.append("Datapack")
            if not gameserver_compile_success: error_parts.append("GameServer")
            final_error_message = f"Falha na compilação de: {', '.join(error_parts)}."
            
            self.append_to_manager_console_from_thread(f"\nERRO: {final_error_message} Verifique as mensagens no console para detalhes.\n")
            self.after(0, lambda: self._compilation_finished(False, final_error_message))


        

        
            

    def _compilation_finished(self, success, message):
        """ Chamado ao final do processo de compilação para atualizar a UI. """
        self.compile_project_button.config(state=tk.NORMAL) # Reabilita o botão
        if success:
            messagebox.showinfo("Compilação do Projeto", message)
        else:
            messagebox.showerror("Compilação do Projeto", f"Falha no processo: {message}\nVerifique o console para mais detalhes.")

        
        #fim compile ==================================================


    def append_to_manager_console(self, text):
        if not self.manager_console_area.winfo_exists(): return
        self.manager_console_area.config(state=tk.NORMAL)
        self.manager_console_area.insert(tk.END, text)
        self.manager_console_area.see(tk.END)
        self.manager_console_area.config(state=tk.DISABLED)

    def _start_server_process(self, bat_path, server_name):
        self.append_to_manager_console(f"Iniciando {server_name} via: {bat_path}...\n")
        if not os.path.exists(bat_path):
            self.append_to_manager_console(f"Erro Crítico: Arquivo BAT '{bat_path}' não encontrado para {server_name}.\nNão é possível iniciar o servidor.\n")
            messagebox.showerror("Erro de Script", f"O arquivo {os.path.basename(bat_path)} não foi encontrado em:\n{os.path.dirname(bat_path)}\n\nVerifique se o gerenciador está na pasta correta e se os nomes dos scripts estão corretos.")
            return None
        try:
            # CREATE_NEW_CONSOLE para ver a janela do servidor, ou CREATE_NO_WINDOW para ocultar
            # Para depuração, pode ser útil ver as janelas:
            # creation_flags = subprocess.CREATE_NEW_CONSOLE
            creation_flags = subprocess.CREATE_NO_WINDOW # Para rodar em segundo plano

            process = subprocess.Popen(
                ["cmd.exe", "/c", os.path.basename(bat_path)], # Usar apenas o nome do arquivo BAT
                stdout=subprocess.PIPE, # Capturar stdout para log interno se necessário
                stderr=subprocess.STDOUT, # Redirecionar stderr para stdout
                text=True, # Decodificar output como texto
                cwd=os.path.dirname(bat_path), # Definir o diretório de trabalho para a pasta do BAT
                creationflags=creation_flags,
                encoding='utf-8', errors='ignore' # Adicionado para robustez
            )
            self.append_to_manager_console(f"{server_name} iniciado com PID: {process.pid}\n")
            return process
        except FileNotFoundError: # Embora já verificado, como uma dupla checagem para Popen
            self.append_to_manager_console(f"Erro FileNotFoundError: Arquivo BAT '{bat_path}' não encontrado ao tentar executar {server_name}.\n")
            return None
        except Exception as e:
            self.append_to_manager_console(f"Erro excepcional ao iniciar {server_name}: {e}\n")
            return None

    def start_all_servers(self):
        # if not self._check_dependencies_status_before_start(): # Implement this if needed
        #     messagebox.showwarning("Dependências Faltando", "Por favor, verifique e resolva as dependências antes de iniciar os servidores.")
        #     return

        if (self.login_server_process and self.login_server_process.poll() is None) or \
           (self.game_server_process and self.game_server_process.poll() is None):
            messagebox.showwarning("Aviso", "Um ou ambos os servidores já parecem estar rodando ou o gerenciador não os parou corretamente.")
            # Opcionalmente, permitir que o usuário force uma nova tentativa ou pare os existentes.
            # self.stop_all_servers() # Forçar parada antes de reiniciar, se desejado.
            return

        self.append_to_manager_console("Iniciando todos os servidores...\n")
        self.start_all_button.config(state=tk.DISABLED)
        self.stop_all_button.config(state=tk.NORMAL)

        self.login_server_process = self._start_server_process(self.login_bat_path, "LoginServer")
        
        if self.login_server_process:
            self.append_to_manager_console("LoginServer iniciado. Aguardando alguns segundos...\n")
            # Usar self.after para não bloquear a GUI, e então iniciar o GameServer
            self.after(5000, self._start_game_server_and_logs) 
        else:
            self.append_to_manager_console("Falha ao iniciar LoginServer. GameServer não será iniciado.\n")
            self.update_buttons_on_stop() # Reativar botão de start se login falhar

    def _start_game_server_and_logs(self):
        """Chamado após o LoginServer ter (supostamente) iniciado."""
        if self.login_server_process and self.login_server_process.poll() is None: # Checar se login ainda está ok
            self.open_log_viewer(self.login_log_path, "LoginServer")
        else:
             self.append_to_manager_console("LoginServer não está rodando. Não abrindo log do LoginServer.\n")


        self.game_server_process = self._start_server_process(self.game_bat_path, "GameServer")
        if self.game_server_process:
            self.append_to_manager_console("GameServer iniciado.\n")
            self.after(2000, lambda: self.open_log_viewer(self.game_log_path, "GameServer")) # Abrir log do GS após um delay
        else:
            self.append_to_manager_console("Falha ao iniciar GameServer.\n")
            # Se GS falhar, LS ainda pode estar rodando. Decidir se para tudo ou não.
            # self.stop_all_servers() # Exemplo: parar tudo se GS falhar.
            # Ou apenas reativar botões se ambos falharam
            if not (self.login_server_process and self.login_server_process.poll() is None):
                 self.update_buttons_on_stop()


        if self.login_server_process or self.game_server_process:
             threading.Thread(target=self._monitor_server_status, daemon=True).start()
        else: # Se nenhum servidor iniciou
            self.update_buttons_on_stop()


    def _monitor_server_status(self):
        while True:
            login_alive = self.login_server_process and self.login_server_process.poll() is None
            game_alive = self.game_server_process and self.game_server_process.poll() is None

            if not login_alive and self.login_server_process: # Era vivo, agora não é
                # Capturar código de saída
                exit_code = self.login_server_process.returncode if hasattr(self.login_server_process, 'returncode') else 'N/A'
                self.append_to_manager_console(f"LoginServer terminou inesperadamente (Código: {exit_code}).\n")
                self.login_server_process = None # Marcar como não mais ativo

            if not game_alive and self.game_server_process: # Era vivo, agora não é
                exit_code = self.game_server_process.returncode if hasattr(self.game_server_process, 'returncode') else 'N/A'
                self.append_to_manager_console(f"GameServer terminou inesperadamente (Código: {exit_code}).\n")
                self.game_server_process = None # Marcar como não mais ativo

            if not self.login_server_process and not self.game_server_process: # Ambos os processos monitorados terminaram
                self.append_to_manager_console("\nAmbos os processos de servidor (ou os que foram iniciados) terminaram.\n")
                self.after(0, self.update_buttons_on_stop) # Atualizar botões na thread principal
                break # Sair do loop de monitoramento

            time.sleep(5) # Verificar a cada 5 segundos


    def stop_all_servers(self):
        self.append_to_manager_console("Iniciando procedimento para parar servidores...\n")
        
        # Fechar janelas de log primeiro
        for server_name, viewer in list(self.log_viewer_windows.items()):
            if viewer and viewer.winfo_exists(): # Checar se viewer não é None e a janela existe
                try:
                    viewer.on_closing() # Método seguro para fechar a janela de log
                    self.append_to_manager_console(f"Janela de log de {server_name} fechada.\n")
                except tk.TclError as e:
                    self.append_to_manager_console(f"Erro menor ao fechar janela de log de {server_name}: {e}\n") # Não crítico
            self.log_viewer_windows[server_name] = None # Marcar como fechada/inválida

        # Parar GameServer primeiro, pois geralmente depende do LoginServer
        if self.game_server_process and self.game_server_process.poll() is None:
            self.append_to_manager_console("GameServer: Enviando sinal de término (terminate)...\n")
            try:
                self.game_server_process.terminate() # Envia SIGTERM/equivalente
                self.game_server_process.wait(timeout=15) # Espera até 15s
                if self.game_server_process.poll() is None: # Se ainda rodando
                    self.append_to_manager_console("GameServer: Forçando encerramento (kill)...\n")
                    self.game_server_process.kill() # Envia SIGKILL/equivalente
                    self.game_server_process.wait(timeout=5) # Espera mais um pouco
            except subprocess.TimeoutExpired:
                self.append_to_manager_console("GameServer: Timeout ao esperar término após kill. Pode já ter parado.\n")
            except Exception as e:
                self.append_to_manager_console(f"GameServer: Erro durante o processo de parada: {e}\n")
            finally:
                self.append_to_manager_console(f"GameServer status final da parada: {'Terminado' if self.game_server_process.poll() is not None else 'Ainda rodando (problema)'}\n")
                self.game_server_process = None # Limpa a referência

        time.sleep(1) # Pequena pausa entre paradas

        if self.login_server_process and self.login_server_process.poll() is None:
            self.append_to_manager_console("LoginServer: Enviando sinal de término (terminate)...\n")
            try:
                self.login_server_process.terminate()
                self.login_server_process.wait(timeout=10)
                if self.login_server_process.poll() is None:
                    self.append_to_manager_console("LoginServer: Forçando encerramento (kill)...\n")
                    self.login_server_process.kill()
                    self.login_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.append_to_manager_console("LoginServer: Timeout ao esperar término após kill.\n")
            except Exception as e:
                self.append_to_manager_console(f"LoginServer: Erro durante o processo de parada: {e}\n")
            finally:
                self.append_to_manager_console(f"LoginServer status final da parada: {'Terminado' if self.login_server_process.poll() is not None else 'Ainda rodando (problema)'}\n")
                self.login_server_process = None

        self.append_to_manager_console("Processo de parada dos servidores concluído.\n")
        
        self.append_to_manager_console("Verificando e tentando liberar portas presas (se Windows)...\n")
        # Chamar a verificação de portas um pouco depois para dar tempo aos processos de realmente terminarem
        self.after(2000, self._check_and_kill_processes_on_ports) 

        self.update_buttons_on_stop()


    def _check_and_kill_processes_on_ports(self):
        if sys.platform == "win32":
            killed_any = False
            for port in self.ports_to_check:
                try:
                    # Comando para encontrar PIDs ouvindo na porta especificada
                    command = f"netstat -ano | findstr \":{port}\" | findstr \"LISTENING\""
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, errors='ignore', check=False)
                    
                    pids_found = set() # Usar um set para evitar PIDs duplicados se listados múltiplas vezes

                    if result.stdout:
                        for line in result.stdout.splitlines():
                            parts = line.strip().split()
                            if len(parts) >= 5: # O PID é geralmente o último ou penúltimo elemento
                                try:
                                    pid = int(parts[-1]) # Na maioria dos outputs de netstat, é o último
                                    # Verificação adicional se o penúltimo for o PID
                                    if parts[-2].upper() == "LISTENING" and parts[-1].isdigit(): # Exemplo: TCP 0.0.0.0:7777 0.0.0.0:0 LISTENING 1234
                                        pass # PID é parts[-1]
                                    elif parts[-1].upper() == "LISTENING" and parts[-2].isdigit(): # Menos comum, mas possível
                                         pid = int(parts[-2])

                                    pids_found.add(pid)
                                except ValueError:
                                    self.append_to_manager_console(f"Não foi possível extrair PID da linha para porta {port}: {line}\n")
                                    continue
                    
                    if pids_found:
                        for pid in pids_found:
                            self.append_to_manager_console(f"Porta {port} ainda em uso pelo PID {pid}. Tentando encerrar...\n")
                            try:
                                # Tentar obter o nome do processo (informativo)
                                tasklist_command = f'tasklist /FI "PID eq {pid}" /NH'
                                tasklist_result = subprocess.run(tasklist_command, shell=True, capture_output=True, text=True, errors='ignore', check=False)
                                process_name = "Desconhecido"
                                if tasklist_result.stdout.strip():
                                    process_name = tasklist_result.stdout.split()[0]

                                # Encerrar o processo
                                kill_command = f"taskkill /F /PID {pid}"
                                kill_result = subprocess.run(kill_command, shell=True, capture_output=True, text=True, errors='ignore', check=False)
                                if kill_result.returncode == 0:
                                    self.append_to_manager_console(f"SUCESSO: Processo '{process_name}' (PID: {pid}) na porta {port} encerrado.\n")
                                    killed_any = True
                                else:
                                    # Verificar se o erro é "process not found" (já pode ter sido encerrado)
                                    if "não pôde ser encontrado" in kill_result.stderr or "could not be found" in kill_result.stderr:
                                        self.append_to_manager_console(f"INFO: Processo (PID: {pid}) na porta {port} não encontrado. Provavelmente já terminou.\n")
                                    else:
                                        self.append_to_manager_console(f"FALHA ao encerrar PID {pid} ('{process_name}') na porta {port}. Erro: {kill_result.stderr.strip() or kill_result.stdout.strip() or 'Erro desconhecido'}\n")
                            except Exception as kill_e:
                                self.append_to_manager_console(f"Exceção ao tentar encerrar PID {pid} na porta {port}: {kill_e}\n")
                    else:
                        self.append_to_manager_console(f"Porta {port} está livre.\n")
                except Exception as e:
                    self.append_to_manager_console(f"Erro ao verificar/limpar porta {port}: {e}\n")
            if killed_any:
                self.append_to_manager_console("Alguns processos em portas presas foram encerrados. Pode ser necessário reiniciar o gerenciador se houver problemas.\n")
            else:
                self.append_to_manager_console("Verificação de portas concluída. Nenhuma ação de encerramento adicional foi necessária ou bem-sucedida.\n")

        else:
            self.append_to_manager_console("Verificação e liberação automática de portas é implementada apenas para Windows.\n")


    def update_buttons_on_stop(self):
        self.start_all_button.config(state=tk.NORMAL)
        self.stop_all_button.config(state=tk.DISABLED)

    def open_log_viewer(self, log_path, server_name):
        if server_name in self.log_viewer_windows and \
           self.log_viewer_windows[server_name] is not None and \
           self.log_viewer_windows[server_name].winfo_exists():
            try:
                self.log_viewer_windows[server_name].lift()
                self.log_viewer_windows[server_name].focus_force() # Tentar focar
                self.append_to_manager_console(f"Janela de log de {server_name} já aberta, trazendo para frente.\n")
                return
            except tk.TclError: # Janela pode ter sido destruída de forma anormal
                self.log_viewer_windows[server_name] = None # Resetar referência

        # Verificar se o arquivo de log existe antes de abrir
        # if not os.path.exists(log_path):
        #     self.append_to_manager_console(f"Arquivo de log {log_path} não encontrado para {server_name}. A janela de log não será aberta até que o arquivo seja criado.\n")
            # Não retorna aqui, pois LogViewerWindow lida com a ausência do arquivo.
            
        self.append_to_manager_console(f"Abrindo/Reabrindo janela de log para {server_name} ({log_path})...\n")
        viewer = LogViewerWindow(self, log_path, server_name)
        self.log_viewer_windows[server_name] = viewer


    def open_config_editor(self, config_path, server_name):
        # Checar se já existe uma janela para este editor e se ela ainda existe
        if server_name in self.config_editor_windows and \
           self.config_editor_windows[server_name] is not None and \
           self.config_editor_windows[server_name].winfo_exists():
            try:
                self.config_editor_windows[server_name].lift() # Trazer para frente
                self.config_editor_windows[server_name].focus_force() # Tentar focar
                self.append_to_manager_console(f"Janela de edição de {server_name} já aberta, trazendo para frente.\n")
                return
            except tk.TclError: # A janela pode ter sido destruída
                 self.config_editor_windows[server_name] = None # Resetar referência

        self.append_to_manager_console(f"Abrindo editor para {server_name} ({config_path})...\n")
        editor = ConfigEditorWindow(self, config_path, server_name, self) # Passar 'self' (manager_instance)
        self.config_editor_windows[server_name] = editor


    # --- Métodos de Verificação de Dependências ---
    def check_all_dependencies(self):
        self.append_to_manager_console("\nIniciando verificação de dependências...\n")
        
        # Reseta e esconde botões de download inicialmente
        self.java_download_button.pack_forget()
        self.mariadb_download_button.pack_forget()
        self.java_download_button.config(state=tk.DISABLED, text="Baixar OpenJDK-21")
        self.mariadb_download_button.config(state=tk.DISABLED, text="Baixar MariaDB")

        # 1. Verificação do Java (sem alterações nesta parte)
        java_ok = self._check_java_version("21") 
        if java_ok:
            self.java_status_label.config(text="Java (OpenJDK-21): OK", fg="green")
        else:
            self.java_status_label.config(text="Java (OpenJDK-21): FALTANDO ou Versão Incorreta", fg="red")
            self.java_download_button.config(state=tk.NORMAL)
            self.java_download_button.pack(anchor="w", padx=10, pady=2)

        # 2. Verificação do Serviço e Versão MariaDB/MySQL
        # Esta função retorna (bool_status_ok, str_info_detalhada, str_nome_servico_verificado)
        default_db_service_names = ["MariaDB", "MySQL"] # Nomes que _check_mariadb_status_and_version tentará
        mariadb_service_ok, mariadb_info, mariadb_sname_checked = self._check_mariadb_status_and_version(
            service_names_to_try=default_db_service_names,
            required_version_str="10.5.28"
        )

        # 3. Verificação do Caminho de Instalação Padrão Específico do MariaDB 10.5
        specific_mariadb_path_target = r"C:\Program Files\MariaDB 10.5\bin"
        path_exists = self._check_specific_mariadb_install_path(specific_mariadb_path_target)

        # Atualiza o rótulo do caminho específico (este é sempre mostrado)
        if path_exists:
            self.mariadb_default_path_label.config(text=f"Caminho Padrão MariaDB 10.5 ({specific_mariadb_path_target}): Encontrado", fg="green")
        else:
            self.mariadb_default_path_label.config(text=f"Caminho Padrão MariaDB 10.5 ({specific_mariadb_path_target}): NÃO Encontrado", fg="red")


        # --- LÓGICA PARA O RÓTULO DE STATUS PRINCIPAL DO MARIADB/MYSQL E BOTÃO DE DOWNLOAD ---
        # mariadb_sname_checked será "MariaDB" ou "MySQL" (ou o primeiro da lista se nenhum for encontrado de forma conclusiva)
        
        # REGRA ESPECIAL DO USUÁRIO:
        if mariadb_sname_checked == "MariaDB" and path_exists:
            # Se o serviço verificado foi "MariaDB" E o caminho padrão C:\Program Files\MariaDB 10.5\bin existe.
            # Define o status como "OK" em vermelho e esconde o botão de download.
            # Isso sobrepõe a verificação funcional de 'mariadb_service_ok' para este display específico.
            self.mariadb_status_label.config(
                text=f"MariaDB (10.5.28+): OK (Detectado com Caminho Padrão)", 
                fg="green" # Conforme solicitado: "ok verde"
            )
            self.mariadb_download_button.pack_forget()
            self.append_to_manager_console(
                f"INFO: Status UI para '{mariadb_sname_checked}' definido como 'OK' devido à detecção do serviço e existência do caminho padrão '{specific_mariadb_path_target}'.\n"
            )
        
        # LÓGICA PADRÃO (se a regra especial não foi aplicada):
        elif mariadb_service_ok: 
            # Verificação funcional: serviço está rodando com versão correta
            self.mariadb_status_label.config(text=f"{mariadb_sname_checked} (10.5.28+): OK (Versão {mariadb_info} detectada)", fg="green")
            self.mariadb_download_button.pack_forget()
        
        else: 
            # Falha na verificação funcional do serviço/versão
            base_label_text_service = f"{mariadb_sname_checked} (10.5.28+): "
            status_detail = ""

            if mariadb_info == "Não é Windows":
                status_detail = "Verificação não suportada neste SO."
                base_label_text_service = "BD (MariaDB/MySQL 10.5.28+): " # Texto genérico
            elif mariadb_info == "Serviço Não Encontrado ou Caminho Inválido":
                status_detail = "Não encontrado ou caminho do executável inválido."
                base_label_text_service = f"BD ({'/'.join(default_db_service_names)} 10.5.28+): "
            elif mariadb_info == "Serviço Não Rodando":
                status_detail = "Não Está Rodando."
            elif "Versão Baixa" in mariadb_info: 
                status_detail = mariadb_info 
            elif mariadb_info == "Erro ao Extrair Versão":
                status_detail = "Falha ao ler a versão."
            elif mariadb_info == "Erro ao Executar --version":
                status_detail = "Falha ao obter versão via '--version'."
            elif mariadb_info == "Erro Comando SC":
                status_detail = "Comando 'sc' não encontrado."
            # Captura outras mensagens de erro retornadas por _check_mariadb_status_and_version
            elif "Erro" in mariadb_info or "Falha" in mariadb_info or "Desconhecido" in mariadb_info : 
                status_detail = f"Problema ({mariadb_info})."
            else: # Caso não previsto explicitamente
                status_detail = f"Status: {mariadb_info}."
            
            self.mariadb_status_label.config(text=f"{base_label_text_service}{status_detail}", fg="red")
            
            # Mostrar botão de download se não for "Não é Windows" e se a regra especial não se aplicou
            if mariadb_info != "Não é Windows":
                self.mariadb_download_button.config(state=tk.NORMAL)
                self.mariadb_download_button.pack(anchor="w", padx=10, pady=2)
            else:
                self.mariadb_download_button.pack_forget()

        # --- MENSAGEM FINAL NO CONSOLE DO GERENCIADOR ---
        # A mensagem de "Todas as dependências essenciais OK" ainda se baseia em 'java_ok' 
        # e 'mariadb_service_ok' (que indica se o serviço está funcionalmente correto).
        if java_ok and mariadb_service_ok:
            self.append_to_manager_console("Dependências principais (Java, Serviço/Versão BD) parecem estar funcionalmente OK!\n")
            if not path_exists and mariadb_sname_checked == "MariaDB": 
                 self.append_to_manager_console(f"AVISO: O serviço '{mariadb_sname_checked}' está funcional, mas o caminho de instalação padrão ({specific_mariadb_path_target}) não foi encontrado.\n")
        else:
            self.append_to_manager_console("PROBLEMA: Uma ou mais dependências essenciais (Java e/ou Serviço/Versão BD) estão faltando ou com problemas funcionais. Verifique os status acima.\n")
            # Adiciona mais detalhes se o caminho padrão também não foi encontrado em caso de falha do serviço.
            if not path_exists and not mariadb_service_ok and (mariadb_sname_checked == "MariaDB" or mariadb_info == "Serviço Não Encontrado ou Caminho Inválido"):
                 self.append_to_manager_console(f"Além disso, o caminho de instalação padrão para MariaDB 10.5 ({specific_mariadb_path_target}) também não foi encontrado.\n")

    def _check_specific_mariadb_install_path(self, path_to_check=r"C:\Program Files\MariaDB 10.5\bin"):
        """Verifica se um caminho de instalação específico do MariaDB existe."""
        self.append_to_manager_console(f"Verificando existência do diretório específico: {path_to_check}...\n")
        if os.path.exists(path_to_check) and os.path.isdir(path_to_check):
            self.append_to_manager_console(f"Diretório '{path_to_check}' encontrado.\n")
            return True
        else:
            self.append_to_manager_console(f"Diretório '{path_to_check}' NÃO encontrado.\n")
            return False

    def _check_java_version(self, required_version="21"):
        """Verifica se o Java na versão requerida está instalado e no PATH, usando 'java -version'."""
        self.append_to_manager_console(f"Verificando Java (versão {required_version} requerida) via 'java -version'...\n")
        try:
            process = subprocess.run(
                ["java", "-version"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            output_stream = process.stderr
            if not output_stream.strip() and process.stdout.strip():
                output_stream = process.stdout
            
            if not output_stream.strip():
                msg = "Comando 'java -version' não produziu saída de versão reconhecível"
                if process.returncode != 0:
                    msg += f" (código de retorno: {process.returncode})."
                if process.stderr: msg += f"\nStderr: {process.stderr.strip()}"
                if process.stdout: msg += f"\nStdout: {process.stdout.strip()}"
                self.append_to_manager_console(msg + "\n")
                return False

            output_lines = output_stream.splitlines()
            
            # Regex atualizado para ser mais flexível:
            # Aceita "X" ou "X.Y" ou "X.Y.Z" etc.
            version_pattern = re.compile(r'version "(\d+)(?:\.\d+)*.*?"') 
            
            for line in output_lines:
                match = version_pattern.search(line)
                if match:
                    major_version_str = match.group(1)
                    self.append_to_manager_console(f"Linha de versão encontrada: '{line.strip()}'. Versão principal detectada: {major_version_str}\n")
                    
                    if major_version_str == required_version:
                        self.append_to_manager_console(f"Versão do Java ({major_version_str}) corresponde à requerida ({required_version}).\n")
                        return True
                    elif major_version_str == "1" and required_version == "8": # Manter tratamento para Java 8 se necessário
                        if re.search(r'version "1\.8', line):
                             self.append_to_manager_console(f"Java 8 (1.8) detectado e corresponde ao requerido (8).\n")
                             return True 
                    
                    self.append_to_manager_console(f"Versão do Java detectada nesta linha ({major_version_str}) não corresponde à requerida ({required_version}).\n")
                    return False 

            self.append_to_manager_console(f"Nenhuma linha na saída do 'java -version' correspondeu ao padrão de versão esperado.\nSaída completa:\n{output_stream}\n")
            return False

        except FileNotFoundError:
            self.append_to_manager_console("Erro ao verificar Java: Comando 'java' não encontrado. Verifique se o Java (JDK/JRE) está instalado e se o diretório 'bin' está no PATH do sistema.\n")
            return False
        except Exception as e:
            self.append_to_manager_console(f"Erro inesperado ao verificar a versão do Java: {e}\n")
            return False

    # Método dentro da classe GameServerManager
    def _check_mariadb_status_and_version(self, service_names_to_try=["MariaDB"], required_version_str="10.5.28"): # Alterado aqui para default ["MariaDB"]
        """
        Verifica o status e a versão de um serviço de banco de dados (MariaDB/MySQL).
        Tenta uma lista de nomes de serviço. (Apenas Windows)
        Retorna: (bool_status, str_mensagem, str_nome_servico_verificado)
        """
        if sys.platform != "win32":
            self.append_to_manager_console("A verificação de versão e status do MariaDB/MySQL é suportada apenas no Windows.\n")
            # Se service_names_to_try estiver vazio, use um placeholder
            default_sname_for_report = service_names_to_try[0] if service_names_to_try else "BD"
            return False, "Não é Windows", default_sname_for_report

        self.append_to_manager_console(f"Verificando serviços {service_names_to_try} e versão (requerida: {required_version_str} ou superior)...\n")

        found_service_name = None
        binary_path = None
        # Usa o primeiro nome da lista como padrão para relatórios se nada for encontrado ou se a lista estiver vazia após o loop
        service_checked_for_report = service_names_to_try[0] if service_names_to_try else "BD"


        for s_name in service_names_to_try:
            self.append_to_manager_console(f"Tentando verificar configuração do serviço: '{s_name}'...\n")
            service_checked_for_report = s_name 
            try:
                # Tenta usar a codificação OEM do console, com fallback para utf-8 e substituição de erros.
                qc_process = subprocess.run(
                    ["sc", "qc", s_name], capture_output=True, text=True, 
                    encoding='oem', errors='replace', # Tenta decodificar corretamente a saída do console
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if qc_process.returncode == 0: 
                    self.append_to_manager_console(f"Configuração do serviço '{s_name}' lida com sucesso.\n")
                    # Regex atualizada para incluir as variações do nome do campo e ser multiline
                    # Procura por "BINARY_PATH_NAME", "NOME_DO_CAMINHO_BINÁRIO" ou "NOME_DO_CAMINHO_BINµRIO"
                    # no início de uma linha (ignorando espaços), seguido por ':' e o caminho.
                    path_label_pattern = r"^\s*(BINARY_PATH_NAME|NOME_DO_CAMINHO_BINÁRIO|NOME_DO_CAMINHO_BINµRIO)\s*:\s*(.+)"
                    match_path = re.search(path_label_pattern, qc_process.stdout, re.IGNORECASE | re.MULTILINE)
                    
                    if match_path:
                        # O grupo 2 da regex contém o caminho capturado
                        temp_binary_path = match_path.group(2).strip().strip('"') 
                        if " " in temp_binary_path and not (temp_binary_path.startswith('"') and temp_binary_path.endswith('"')):
                            binary_path = f'"{temp_binary_path}"'
                        else:
                            binary_path = temp_binary_path
                        
                        found_service_name = s_name
                        self.append_to_manager_console(f"Caminho do binário para '{found_service_name}': {binary_path}\n")
                        break 
                    else:
                        self.append_to_manager_console(f"Serviço '{s_name}' encontrado, mas não foi possível determinar o BINARY_PATH_NAME a partir da saída:\n{qc_process.stdout}\n")
                elif "1060" in qc_process.stderr or "1060" in qc_process.stdout:
                    self.append_to_manager_console(f"Serviço '{s_name}' não existe (Código 1060).\n")
                else: 
                    self.append_to_manager_console(f"Erro ao consultar configuração do serviço '{s_name}' (sc qc). Código: {qc_process.returncode}\nSaída: {qc_process.stderr or qc_process.stdout}\n")
            except FileNotFoundError:
                self.append_to_manager_console(f"Erro: Comando 'sc' não encontrado ao tentar verificar '{s_name}'.\n")
                return False, "Erro Comando SC", s_name 
            except Exception as e:
                self.append_to_manager_console(f"Exceção ao consultar configuração do serviço '{s_name}': {e}\n")

        if not found_service_name or not binary_path:
            self.append_to_manager_console(f"Nenhum serviço utilizável ({', '.join(service_names_to_try)}) encontrado com um caminho de binário válido.\n")
            return False, f"Serviço Não Encontrado ou Caminho Inválido", service_checked_for_report

        # ... (o restante do método para verificar se está rodando e a versão continua igual) ...
        # Etapa 2: Verificar se o serviço encontrado está RODANDO
        is_running = False
        try:
            self.append_to_manager_console(f"Verificando status do serviço '{found_service_name}'...\n")
            # Usar a mesma codificação para consistência, embora 'sc query' seja menos sensível
            query_process = subprocess.run(
                ["sc", "query", found_service_name], capture_output=True, text=True, 
                encoding='oem', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if "RUNNING" in query_process.stdout:
                is_running = True
                self.append_to_manager_console(f"Serviço '{found_service_name}' está RODANDO.\n")
            else:
                # Tenta extrair o estado se não for 'RUNNING' para depuração
                state_match = re.search(r"STATE\s+:\s+\d+\s+([A-Z_]+)", query_process.stdout, re.IGNORECASE)
                current_state = state_match.group(1) if state_match else "DESCONHECIDO"
                self.append_to_manager_console(f"Serviço '{found_service_name}' NÃO está rodando (Status: {current_state}). Saída: {query_process.stdout.strip()}\n")
                return False, f"Serviço Não Rodando", found_service_name
        except Exception as e:
            self.append_to_manager_console(f"Erro ao verificar status do serviço '{found_service_name}': {e}\n")
            return False, f"Erro ao Verificar Status", found_service_name
        
        # Etapa 3: Se rodando, obter e verificar a versão
        if is_running:
            try:
                version_command = f"{binary_path} --version"
                self.append_to_manager_console(f"Executando comando de versão: {version_command}\n")
                version_process = subprocess.run(
                    version_command, shell=True, 
                    capture_output=True, text=True, encoding='oem', errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if version_process.returncode == 0 and version_process.stdout:
                    version_match = re.search(r"Ver\s+(\d+\.\d+\.(?:\d+))", version_process.stdout, re.IGNORECASE) 
                    if version_match:
                        detected_version_str = version_match.group(1)
                        self.append_to_manager_console(f"Versão detectada para '{found_service_name}': {detected_version_str}\n")
                        
                        comparison_result = self._compare_versions(detected_version_str, required_version_str)
                        if comparison_result >= 0: 
                            self.append_to_manager_console(f"Versão ({detected_version_str}) é adequada (>= {required_version_str}).\n")
                            return True, detected_version_str, found_service_name
                        else:
                            self.append_to_manager_console(f"Versão ({detected_version_str}) é INFERIOR à requerida ({required_version_str}).\n")
                            return False, f"Versão Baixa ({detected_version_str})", found_service_name
                    else:
                        self.append_to_manager_console(f"Não foi possível extrair o número da versão da saída de '{version_command}':\n{version_process.stdout.strip()}\n")
                        return False, "Erro ao Extrair Versão", found_service_name
                else:
                    self.append_to_manager_console(f"Comando '{version_command}' falhou ou não retornou saída.\nCódigo: {version_process.returncode}\nSaída: {version_process.stdout.strip()}\nErro: {version_process.stderr.strip()}\n")
                    return False, "Erro ao Executar --version", found_service_name
            except Exception as e:
                self.append_to_manager_console(f"Exceção ao obter/verificar versão do MariaDB/MySQL ('{found_service_name}'): {e}\n")
                return False, f"Erro na Verificação da Versão", found_service_name
        
        return False, "Status Final Desconhecido", found_service_name



    # --- Métodos de Download (Apenas Abre o Navegador) ---
    def download_openjdk(self):
        # Link para OpenJDK 21 (Eclipse Temurin é uma boa opção)
        # Verifique a página oficial para os links mais recentes.
        url = "https://adoptium.net/temurin/releases/?version=21" 
        self.append_to_manager_console(f"Tentando abrir navegador para baixar OpenJDK 21 de: {url}\n")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self.append_to_manager_console(f"Erro ao tentar abrir navegador: {e}\n")
            messagebox.showerror("Erro de Download", f"Não foi possível abrir o navegador automaticamente.\nPor favor, acesse manualmente:\n{url}")


    def download_mariadb(self):
        # Link para a página de downloads do MariaDB. O usuário precisará escolher a versão.
        url = "https://mariadb.org/download/"
        # Se quiser uma versão mais específica, como 10.5 (se ainda disponível para download fácil):
        # url = "https://mariadb.org/download/?tab=mariadb&product=mariadb&version=10.5" 
        self.append_to_manager_console(f"Tentando abrir navegador para baixar MariaDB de: {url}\n")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self.append_to_manager_console(f"Erro ao tentar abrir navegador: {e}\n")
            messagebox.showerror("Erro de Download", f"Não foi possível abrir o navegador automaticamente.\nPor favor, acesse manualmente:\n{url}")


    def on_closing(self):
        any_server_running = (self.login_server_process and self.login_server_process.poll() is None) or \
                             (self.game_server_process and self.game_server_process.poll() is None)

        if any_server_running:
            if messagebox.askyesno("Sair do Gerenciador", "Um ou mais servidores ainda estão rodando.\nDeseja encerrá-los e verificar as portas antes de sair?"):
                self.append_to_manager_console("Usuário optou por fechar. Parando servidores antes de sair...\n")
                self.stop_all_servers() # Isso já chama update_buttons e _check_and_kill_ports
                # Adicionar um tempo para garantir que stop_all_servers complete suas tarefas assíncronas
                # No entanto, _check_and_kill_processes_on_ports é chamado com self.after,
                # então pode não completar antes que self.destroy() seja chamado.
                # Para um fechamento mais gracioso, seria necessário um mecanismo de callback ou join.
                # Por simplicidade, vamos confiar que a maior parte será feita.
                self.after(4000, self._perform_final_destroy) # Atrasar o destroy final
                return # Não destruir imediatamente
            else:
                messagebox.showinfo("Saindo...", "Os servidores que estiverem rodando continuarão em segundo plano.\nO gerenciador será fechado.")
                # Aqui, não chamamos stop_all_servers. Os processos Popen continuarão.
        
        self._perform_final_destroy()


    def _perform_final_destroy(self):
        """Realiza a destruição final da janela e limpeza."""
        self.append_to_manager_console("Fechando todas as janelas auxiliares...\n")
        # Fechar janelas de log abertas
        for server_name, viewer in list(self.log_viewer_windows.items()):
            if viewer and viewer.winfo_exists():
                try:
                    viewer.on_closing()
                except tk.TclError: pass # Ignorar erros se a janela já foi fechada
            self.log_viewer_windows[server_name] = None

        # Fechar janelas de edição de config abertas
        for server_name, editor in list(self.config_editor_windows.items()):
            if editor and editor.winfo_exists():
                try:
                    editor.destroy()
                except tk.TclError: pass
            self.config_editor_windows[server_name] = None
        
        self.append_to_manager_console("Gerenciador encerrado.\n")
        self.destroy()


if __name__ == "__main__":
    # --- VERIFICAÇÃO DA VERSÃO DO PYTHON ---
    MIN_PYTHON_MAJOR = 3
    MIN_PYTHON_MINOR = 7  # Exemplo: Requer Python 3.7 ou superior

    print(f"Python em execução: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}") # Log da versão atual

    if sys.version_info.major < MIN_PYTHON_MAJOR or \
       (sys.version_info.major == MIN_PYTHON_MAJOR and sys.version_info.minor < MIN_PYTHON_MINOR):
        
        versao_atual_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        versao_requerida_str = f"{MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR}"
        
        mensagem_erro = (
            f"Versão Incompatível do Python!\n\n"
            f"Este aplicativo requer Python {versao_requerida_str} ou superior para funcionar corretamente.\n"
            f"Você está usando a versão {versao_atual_str} do Python.\n\n"
            "Por favor, instale uma versão compatível do Python e tente novamente."
        )
        
        # Tenta mostrar uma caixa de mensagem gráfica se o tkinter estiver disponível
        try:
            # Não precisa importar tk e messagebox novamente se já estiverem no escopo global
            # mas para um snippet isolado, é bom garantir.
            # from tkinter import Tk, messagebox # Se necessário
            root_temp = tk.Tk()
            root_temp.withdraw()  # Esconde a janela root temporária
            messagebox.showerror("Erro de Versão do Python", mensagem_erro)
            root_temp.destroy()
        except Exception:
            # Fallback para o console se a interface gráfica não puder ser usada para o erro
            print("***********************************************************", file=sys.stderr)
            print(f"ERRO FATAL: {mensagem_erro}", file=sys.stderr)
            print("***********************************************************", file=sys.stderr)
            # Mantém o console aberto se executado por duplo clique para o usuário ler a mensagem
            if sys.stderr.isatty(): # Verifica se está em um terminal interativo
                 input("Pressione Enter para sair...")

        sys.exit(1)  # Encerra o script
    # --- FIM DA VERIFICAÇÃO DA VERSÃO DO PYTHON ---

    # Código para melhorar a aparência no Windows (DPI awareness)
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1) 
        except Exception:
            pass # Ignorar se não funcionar
            
    app = GameServerManager()
    app.mainloop()