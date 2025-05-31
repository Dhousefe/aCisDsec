import tkinter as tk
from tkinter import scrolledtext, messagebox, font as tkFont, filedialog, ttk
import subprocess
import threading
import os
import time
import sys
import re
import shutil
import requests

def _check_command_is_available(command_parts_list, version_arg="--version"):
    """Verifica se um comando está disponível no PATH e é executável."""
    try:
        cmd_to_run = command_parts_list
        if version_arg: # Se um argumento de versão é fornecido, adicione-o
            cmd_to_run = command_parts_list + [version_arg]

        process = subprocess.run(
            cmd_to_run,
            capture_output=True, text=True, check=True,
            encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        # Extrai a primeira linha da saída da versão para log, se houver
        first_line_output = process.stdout.strip().splitlines()[0] if process.stdout.strip() else "N/A (sem saída de versão)"
        print(f"INFO: Comando '{command_parts_list[0]}' encontrado. Saída da verificação: {first_line_output}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"AVISO: Comando '{command_parts_list[0]}' não encontrado ou falhou. Erro: {e}")
        return False
    except Exception as e_gen: # Captura outras exceções potenciais
        print(f"AVISO: Exceção inesperada ao verificar comando '{command_parts_list[0]}': {e_gen}")
        return False


def ensure_git_is_available():
    """
    Verifica se o Git está instalado e acessível.
    Se não estiver, informa o usuário com instruções.
    Retorna True se o Git estiver disponível, False caso contrário.
    """
    print("Verificando disponibilidade do Git...")
    if _check_command_is_available(["git"]): # A função _check_command_is_available usa --version por padrão
        print("INFO: Git está instalado e acessível no PATH.")
        return True
    else:
        print("ERRO: Git não encontrado no PATH do sistema.")
        mensagem_erro_git = (
            "O Git não foi encontrado no seu sistema ou não está configurado no PATH.\n\n"
            "O Git é necessário para baixar e atualizar o código fonte do projeto para compilação.\n\n"
            "Por favor, instale o Git a partir do site oficial:\n"
            "https://git-scm.com/downloads\n\n"
            "Durante a instalação no Windows, certifique-se de selecionar uma opção que adicione o Git ao PATH, "
            "como por exemplo: 'Git from the command line and also from 3rd-party software' ou similar.\n\n"
            "Após a instalação, pode ser necessário reiniciar este aplicativo ou o seu computador."
        )
        
        temp_root_for_prompt = None
        try:
            if not tk._default_root: 
                temp_root_for_prompt = tk.Tk()
                temp_root_for_prompt.withdraw()
            
            messagebox.showerror("Git Não Encontrado", mensagem_erro_git, parent=temp_root_for_prompt)

        except Exception as e_tk:
            # Fallback para o console se a interface gráfica não puder ser usada para o erro
            print("***********************************************************", file=sys.stderr)
            print(f"ERRO CRÍTICO (Git): {mensagem_erro_git}", file=sys.stderr)
            print("***********************************************************", file=sys.stderr)
            if sys.stdin.isatty(): # Verifica se está em um terminal interativo
                 input("Pressione Enter para continuar (funcionalidade Git estará desabilitada)...")
        finally:
            if temp_root_for_prompt:
                temp_root_for_prompt.destroy()
            
        return False # Git não está disponível

# --- FUNÇÃO AUXILIAR PARA CAMINHOS DE RECURSOS (ÍCONE, ETC.) ---
# (Sua função resource_path aqui...)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- FUNÇÕES PARA VERIFICAR E INSTALAR 'requests' ---
def _install_package_via_pip(package_name):
    """Tenta instalar um pacote Python usando pip."""
    try:
        # sys.executable garante que estamos usando o pip do interpretador Python atual
        print(f"Tentando instalar o pacote '{package_name}' via pip...")
        # Usamos check=False para poder capturar e exibir erros de forma mais controlada
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True, check=False,
            encoding='utf-8', errors='replace' # Adicionado encoding para consistência
        )
        if result.returncode == 0:
            print(f"Pacote '{package_name}' parece ter sido instalado com sucesso.")
            # Importante: Após a instalação, a nova biblioteca pode não estar imediatamente
            # disponível para importação no mesmo processo/script sem reiniciar ou truques.
            # A verificação de importação deve ser feita após uma nova tentativa de import.
            return True
        else:
            print(f"ERRO ao tentar instalar '{package_name}'. Código de saída: {result.returncode}")
            print(f"Saída do Pip (stdout):\n{result.stdout}")
            print(f"Saída de Erro do Pip (stderr):\n{result.stderr}")
            return False
    except Exception as e:
        print(f"Exceção ao tentar instalar '{package_name}' via pip: {e}")
        return False

def ensure_requests_library_installed():
    """
    Verifica se a biblioteca 'requests' está instalada.
    Se não estiver, pergunta ao usuário se deseja instalá-la.
    Retorna True se 'requests' estiver disponível (instalada ou recém-instalada e importável),
    False caso contrário.
    """
    try:
        import requests
        print("INFO: Biblioteca 'requests' já está instalada e disponível.")
        return True
    except ImportError:
        print("AVISO: Biblioteca 'requests' não encontrada.")
        
        # Criar uma janela raiz temporária para o messagebox, se a app principal ainda não iniciou
        temp_root_for_prompt = None
        if not tk._default_root: # Verifica se já existe uma instância Tk root
            temp_root_for_prompt = tk.Tk()
            temp_root_for_prompt.withdraw() # Esconde a janela
        
        user_response = messagebox.askyesno(
            "Dependência Recomendada",
            "A biblioteca 'requests' é recomendada para downloads mais confiáveis (ex: Google Drive).\n"
            "Ela não parece estar instalada no seu ambiente Python.\n\n"
            "Deseja tentar instalá-la agora usando pip?\n"
            "(Requer conexão com a internet e permissões para instalar pacotes Python)",
            parent=temp_root_for_prompt # Garante que a messagebox fique sobre a tela certa
        )

        if temp_root_for_prompt:
            temp_root_for_prompt.destroy()

        if user_response:
            if _install_package_via_pip("requests"):
                # Tenta importar novamente após a instalação
                try:
                    import requests
                    print("INFO: Biblioteca 'requests' instalada e importada com sucesso!")
                    messagebox.showinfo("Instalação Concluída", "'requests' foi instalado com sucesso!")
                    return True
                except ImportError:
                    message = "ERRO: 'requests' foi aparentemente instalado, mas não pôde ser importado.\nPode ser necessário reiniciar o aplicativo."
                    print(message)
                    messagebox.showerror("Erro de Importação Pós-Instalação", message)
                    return False # Falhou em importar após instalar
            else:
                message = "Falha ao instalar 'requests'. A funcionalidade de download pode ser limitada (usará 'urllib' como fallback)."
                print(message)
                messagebox.showwarning("Falha na Instalação", message)
                return False # Falhou em instalar
        else:
            print("INFO: Usuário optou por não instalar 'requests'. Downloads usarão 'urllib.request' como fallback.")
            messagebox.showinfo("Informação", "A instalação de 'requests' foi pulada. Downloads do Google Drive podem ser menos estáveis.")
            return False # Usuário não quis instalar

# ... 

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
        # ... (outras inicializações)
        self.is_git_available = True # Valor padrão, será atualizado após a verificação externa
        # ...
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
        
        self.login_bat_path = os.path.join(self.base_dir, "aCisDsec_project", "Servidor Compilado", "login", "startLoginServer.bat")
        self.game_bat_path = os.path.join(self.base_dir, "aCisDsec_project", "Servidor Compilado", "gameserver", "startGameServer.bat")

        self.game_log_path = os.path.join(self.base_dir, "aCisDsec_project", "Servidor Compilado", "gameserver", "log", "game_server.log") # NOVO CAMINHO CORRETO

        self.login_log_path = os.path.join(self.base_dir, "aCisDsec_project", "Servidor Compilado", "login", "log", "login_server.log") # NOVO CAMINHO CORRETO

        # Se seus logs têm nomes diferentes ou estão em outros locais, ajuste aqui.
        # self.login_log_path = os.path.join(self.base_dir, "login", "login_server.log") # Original
        # self.game_log_path = os.path.join(self.base_dir, "gameserver", "game_server.log") # Original


        self.login_config_path = os.path.join(self.base_dir, "aCisDsec_project", "Servidor Compilado", "login", "config", "loginserver.properties")
        self.game_config_path = os.path.join(self.base_dir, "aCisDsec_project", "Servidor Compilado", "gameserver", "config", "server.properties")
        
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
        
        
        
        
        # --- Seção: Ações do Projeto (Dependências, Compilação, Preparação) ---
        # O LabelFrame pode continuar como "Ações do Projeto"
        # --- Seção: Ações do Projeto ---
        project_actions_frame = tk.LabelFrame(self, text="Ações do Projeto", padx=10, pady=10)
        project_actions_frame.pack(fill="x", padx=10, pady=5)

        # Sub-frame para alinhar os botões de ação horizontalmente
        action_buttons_subframe = tk.Frame(project_actions_frame)
        action_buttons_subframe.pack(pady=5) # Centraliza o grupo de botões

        # Botão Verificar Dependências
        self.check_deps_button = tk.Button(action_buttons_subframe, text="Verificar Dependências",
                                           command=self.check_all_dependencies,
                                           font=("Arial", 10, "bold"), bg="orange", fg="white")
        self.check_deps_button.pack(side=tk.LEFT, padx=10) 

        # Botão Compilar projeto (git)
        self.compile_project_button = tk.Button(action_buttons_subframe, text="Compilar projeto (git)",
                                                command=self.compile_project_git, 
                                                font=("Arial", 10, "bold"), bg="dodgerblue", fg="white")
        self.compile_project_button.pack(side=tk.LEFT, padx=10)

        # Botão Preparar inicialização
        self.prepare_init_button = tk.Button(action_buttons_subframe, text="Preparar inicialização",
                                              command=self.prepare_initialization, 
                                              font=("Arial", 10, "bold"), bg="seagreen", fg="white")
        self.prepare_init_button.pack(side=tk.LEFT, padx=10)

        # NOVO BOTÃO: Preparar MariaDB
        self.prepare_mariadb_button = tk.Button(action_buttons_subframe, text="Preparar MariaDB",
                                                 command=self.prepare_mariadb, # Novo método de comando
                                                 font=("Arial", 10, "bold"), bg="sandybrown", fg="white") # Estilo de exemplo
        self.prepare_mariadb_button.pack(side=tk.LEFT, padx=10)
        
        # Labels para mostrar o status das dependências (permanecem em project_actions_frame)
        self.java_status_label = tk.Label(project_actions_frame, text="Java (OpenJDK-21): Não Verificado", fg="gray")
        self.java_status_label.pack(anchor="w", padx=10)
        
        self.mariadb_status_label = tk.Label(project_actions_frame, text="BD (MariaDB/MySQL 10.5.28+): Não Verificado", fg="gray")
        self.mariadb_status_label.pack(anchor="w", padx=10)
        
        self.mariadb_default_path_label = tk.Label(project_actions_frame, text="Caminho Padrão MariaDB 10.5: Não Verificado", fg="gray")
        self.mariadb_default_path_label.pack(anchor="w", padx=10)
        
        # Botões de download (declarados aqui, exibição controlada em check_all_dependencies)
        self.java_download_button = tk.Button(project_actions_frame, text="Baixar OpenJDK-21", 
                                              command=self.download_openjdk, state=tk.DISABLED)
        self.mariadb_download_button = tk.Button(project_actions_frame, text="Baixar MariaDB", 
                                                 command=self.download_mariadb, state=tk.DISABLED)

        # ... (restante do método create_widgets, como a manager_console_area) ...



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
        
        
        
    def prepare_mariadb(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.append_to_manager_console(f"[{timestamp}] Comando 'Preparar MariaDB' acionado.\n")

        # !!! Verifique se project_source_dir está definido e existe !!!
        # Este caminho é usado para localizar o aCisDsec.sql
        project_source_dir = os.path.join(self.base_dir, "aCisDsec_project") 
        if not os.path.isdir(project_source_dir):
            messagebox.showerror("Erro de Configuração", 
                                 f"O diretório do projeto fonte '{project_source_dir}' não foi encontrado.\n"
                                 "Execute a etapa de 'Compilar projeto (git)' primeiro ou configure o caminho.")
            self.append_to_manager_console(f"ERRO: Diretório do projeto '{project_source_dir}' não encontrado para 'Preparar MariaDB'.\n")
            return

        sql_script_relative_path = os.path.join("aCis_datapack", "tools", "aCisDsec.sql")
        sql_script_full_path = os.path.join(project_source_dir, sql_script_relative_path)

        if not os.path.isfile(sql_script_full_path):
            messagebox.showerror("Erro de Arquivo", 
                                 f"O script SQL 'aCisDsec.sql' não foi encontrado em:\n"
                                 f"{os.path.join(project_source_dir, 'aCis_datapack', 'tools')}\n\n"
                                 "Verifique se o projeto foi baixado e se o arquivo está no local esperado.")
            self.append_to_manager_console(f"ERRO: Script SQL '{sql_script_full_path}' não encontrado.\n")
            return

        dialog = MariaDBConfigDialog(self)
        db_config = dialog.result # result é preenchido quando o diálogo é fechado via OK/Cancelar

        if db_config:
            self.append_to_manager_console(f"Configurações MariaDB recebidas: Host={db_config['host']}, User={db_config['user']}, DB={db_config['db_name']}\n")
            self.append_to_manager_console(f"Caminho mysql.exe: {db_config['mysql_exe_path']}\n")
            self.append_to_manager_console(f"Script SQL a ser importado: {sql_script_full_path}\n")

            self.prepare_mariadb_button.config(state=tk.DISABLED)
            self._show_loading_modal(title="Preparando Banco de Dados", 
                                     message=f"Importando script SQL para o banco '{db_config['db_name']}'...\nPor favor, aguarde.")
            
            # Iniciar a execução do script SQL em uma thread
            db_thread = threading.Thread(
                target=self._execute_mariadb_script_thread, 
                args=(db_config, sql_script_full_path),
                daemon=True
            )
            db_thread.start()
        else:
            self.append_to_manager_console("Preparação do MariaDB cancelada pelo usuário.\n")



    def _execute_mariadb_script_thread(self, db_config, sql_file_path):
        """
        Cria o banco de dados se não existir e depois importa o script SQL,
        tentando mostrar saída detalhada do mysql.exe.
        Esta função roda em uma thread separada.
        """
        self.append_to_manager_console_from_thread(f"Iniciando preparação do banco de dados: {db_config['db_name']}\n")

        mysql_exe = db_config['mysql_exe_path']
        host = db_config['host']
        user = db_config['user']
        password = db_config['password'] 
        db_name = db_config['db_name']

        process_encoding = 'oem' if sys.platform == "win32" else 'utf-8'
        overall_success_flag = False 
        output_message = f"Falha na preparação do banco de dados '{db_name}'."

        # --- ETAPA 1: CRIAR O BANCO DE DADOS SE NÃO EXISTIR ---
        # (Esta parte permanece como na resposta anterior, pois é rápida e não precisa de streaming complexo)
        self.append_to_manager_console_from_thread(f"Tentando criar o banco de dados '{db_name}' (se não existir)...\n")
        create_db_command = [mysql_exe, "-h", host, "-u", user]
        if password:
            create_db_command.append(f"-p{password}")
        sql_create_db_statement = f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        try:
            process_create_db = subprocess.Popen(
                create_db_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding=process_encoding, errors='replace',
                cwd=os.path.dirname(mysql_exe),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            stdout_cdb, stderr_cdb = process_create_db.communicate(input=sql_create_db_statement, timeout=60)
            if stdout_cdb: self.append_to_manager_console_from_thread(f"Saída (Criar BD) MySQL:\n{stdout_cdb.strip()}\n")
            if stderr_cdb: self.append_to_manager_console_from_thread(f"Alerta/Erro (Criar BD) MySQL:\n{stderr_cdb.strip()}\n")
            if process_create_db.returncode != 0:
                self.append_to_manager_console_from_thread(f"ERRO: Falha ao criar/assegurar BD '{db_name}'. Código: {process_create_db.returncode}.\n")
                output_message = f"Falha ao criar/verificar BD '{db_name}'. {stderr_cdb.strip()}"
                self.after(0, lambda: self._preparation_finished(False, output_message))
                return
            else:
                self.append_to_manager_console_from_thread(f"Banco de dados '{db_name}' verificado/criado.\n")
        except Exception as e_create_db: # Inclui TimeoutExpired de communicate
            self.append_to_manager_console_from_thread(f"ERRO EXCEPCIONAL ao criar BD '{db_name}': {e_create_db}\n")
            output_message = f"Exceção ao criar BD '{db_name}': {e_create_db}"
            self.after(0, lambda: self._preparation_finished(False, output_message))
            return

        # --- ETAPA 2: IMPORTAR O SCRIPT SQL PRINCIPAL COM SAÍDA DETALHADA ---
        self.append_to_manager_console_from_thread(f"\nIniciando importação do script SQL '{os.path.basename(sql_file_path)}' para '{db_name}' (com detalhes)...\n")
        
        import_sql_command = [mysql_exe, "-h", host, "-u", user]
        if password:
            import_sql_command.append(f"-p{password}")
        import_sql_command.extend(["-D", db_name])
        # Adicionar flags de verbosidade. '-v' repetido aumenta a verbosidade.
        import_sql_command.extend(["-v"]) # ou import_sql_command.append("--verbose") 

        try:
            # Esconde a senha do log do comando
            logged_command = list(import_sql_command) # Cria uma cópia
            if password:
                try:
                    idx = logged_command.index(f"-p{password}")
                    logged_command[idx] = "-p********"
                except ValueError: pass # Se -p não estiver no formato esperado, não substitui

            self.append_to_manager_console_from_thread(f"Executando: {' '.join(logged_command)} < {os.path.basename(sql_file_path)}\n")
            
            with open(sql_file_path, 'r', encoding='utf-8', errors='replace') as sql_file_handle:
                process_import_sql = subprocess.Popen(
                    import_sql_command,
                    stdin=sql_file_handle,    # Alimenta o script SQL ao mysql.exe
                    stdout=subprocess.PIPE,   # Captura a saída padrão para streaming
                    stderr=subprocess.PIPE,   # Captura a saída de erro para streaming
                    text=True, 
                    encoding=process_encoding,
                    errors='replace',
                    bufsize=1,                # Buffer por linha para streaming
                    universal_newlines=True,  # Normaliza newlines
                    cwd=os.path.dirname(mysql_exe),
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )

                # Função para ler e encaminhar um stream (stdout ou stderr)
                def stream_pipe_to_console(pipe, pipe_name_prefix):
                    try:
                        with pipe: # Garante que o pipe seja fechado ao sair
                            for line in iter(pipe.readline, ''): # Lê linha por linha até o fim
                                self.append_to_manager_console_from_thread(f"{pipe_name_prefix}: {line.rstrip()}\n")
                    except Exception as e_pipe:
                        self.append_to_manager_console_from_thread(f"Erro lendo {pipe_name_prefix} do mysql.exe: {e_pipe}\n")

                # Cria e inicia threads para ler stdout e stderr em paralelo
                stdout_reader_thread = threading.Thread(target=stream_pipe_to_console, args=(process_import_sql.stdout, "MySQL-Info"), daemon=True)
                stderr_reader_thread = threading.Thread(target=stream_pipe_to_console, args=(process_import_sql.stderr, "MySQL-Erro"), daemon=True)
                
                stdout_reader_thread.start()
                stderr_reader_thread.start()

                # Espera o processo mysql.exe terminar, com timeout
                # Um timeout longo é necessário para importações grandes
                process_timeout_seconds = 1800 # 30 minutos, ajuste conforme necessário
                try:
                    process_import_sql.wait(timeout=process_timeout_seconds)
                except subprocess.TimeoutExpired:
                    self.append_to_manager_console_from_thread(f"ERRO: Timeout ({process_timeout_seconds}s) ao importar script SQL. Processo será finalizado.\n")
                    process_import_sql.kill() # Tenta finalizar o processo
                    # Dê um tempinho para as threads de leitura pegarem as últimas mensagens após o kill
                    stdout_reader_thread.join(timeout=2)
                    stderr_reader_thread.join(timeout=2)
                    output_message = "Timeout durante a importação do SQL."
                    self.after(0, lambda: self._preparation_finished(False, output_message))
                    return

                # Garante que as threads de leitura terminaram
                stdout_reader_thread.join(timeout=5)
                stderr_reader_thread.join(timeout=5)

                if process_import_sql.returncode == 0:
                    self.append_to_manager_console_from_thread(f"Script SQL '{os.path.basename(sql_file_path)}' importado com sucesso para o banco '{db_name}'.\n")
                    overall_success_flag = True
                    output_message = f"Banco de dados '{db_name}' preparado com sucesso!"
                else:
                    self.append_to_manager_console_from_thread(f"ERRO: Falha ao importar script SQL. Código de saída: {process_import_sql.returncode}.\nVerifique as mensagens de erro do MySQL acima.\n")
                    output_message = f"Falha ao importar SQL para '{db_name}'. Código: {process_import_sql.returncode}."
        
        except FileNotFoundError: 
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO: Arquivo SQL '{sql_file_path}' não encontrado.\n")
            output_message = f"Arquivo SQL '{os.path.basename(sql_file_path)}' não encontrado."
        except Exception as e_import_sql:
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO ao executar o script SQL '{os.path.basename(sql_file_path)}': {e_import_sql}\n")
            output_message = f"Erro durante importação do SQL: {e_import_sql}"

        self.after(0, lambda: self._preparation_finished(overall_success_flag, output_message))


        
    def prepare_initialization(self):
        """
        Prepara a estrutura de pastas e arquivos para a inicialização do servidor.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.append_to_manager_console(f"[{timestamp}] Comando 'Preparar inicialização' acionado.\n")

        self.prepare_init_button.config(state=tk.DISABLED) # Desabilita o botão
        self._show_loading_modal(title="Preparando", message="Preparando arquivos para inicialização...\nPor favor, aguarde.")
        
        preparation_thread = threading.Thread(target=self._perform_preparation_thread, daemon=True)
        preparation_thread.start()
        
    
    def _perform_preparation_thread(self):
        project_source_dir = os.path.join(self.base_dir, "aCisDsec_project") 
        compiled_server_dir_name = "Servidor Compilado"
        target_root_dir = os.path.join(project_source_dir, compiled_server_dir_name)
        
        datapack_source_base = os.path.join(project_source_dir, "aCis_datapack", "build")
        gameserver_dist_source_base = os.path.join(project_source_dir, "aCis_gameserver", "build", "dist")

        self.append_to_manager_console_from_thread(f"\n--- Iniciando Preparação para Inicialização ---\n")
        # ... (verificações de project_source_dir e target_root_dir como antes) ...
        if not os.path.isdir(project_source_dir): # Verificação inicial
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO: Diretório do projeto fonte '{project_source_dir}' não encontrado!\nA preparação será abortada.")
            self.after(0, lambda: self._preparation_finished(False, f"Diretório do projeto fonte '{os.path.basename(project_source_dir)}' não encontrado."))
            return
        target_existed_before = os.path.isdir(target_root_dir)
        try:
            os.makedirs(target_root_dir, exist_ok=True)
            self.append_to_manager_console_from_thread(f"Diretório de destino '{target_root_dir}' criado/verificado.\n")
        except Exception as e:
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO ao criar diretório de destino '{target_root_dir}': {e}\n")
            self.after(0, lambda: self._preparation_finished(False, "Falha ao criar diretório de destino."))
            return

        overall_success = True
        errors_occurred = []

        # --- ETAPA 0: DOWNLOAD, DESCOMPRESSÃO E CÓPIA DE ARQUIVOS DO PACOTE GEO/CRESTS ---
        self.append_to_manager_console_from_thread(f"\n--- Etapa 0: Processando pacote GeoData/Crests ---\n")
        
        gdrive_file_url = "https://drive.google.com/file/d/1iU5x4YkNzWblENUSwHDTlB4SHRxxeaSC/view?usp=sharing"
        download_filename = "geo_crests_package.7z"
        persistent_downloads_dir = os.path.join(project_source_dir, "_arquivos_baixados_servidor")
        os.makedirs(persistent_downloads_dir, exist_ok=True)
        downloaded_7z_file_path = os.path.join(persistent_downloads_dir, download_filename)
        
        # ETAPA 0.A: Download do pacote (como antes)
        if os.path.exists(downloaded_7z_file_path):
            self.append_to_manager_console_from_thread(f"INFO: Arquivo '{download_filename}' já existe. Download pulado.\n")
        else:
            self.append_to_manager_console_from_thread(f"Baixando '{download_filename}'...\n")
            download_ok = self._download_gdrive_file(gdrive_file_url, downloaded_7z_file_path)
            if not download_ok:
                errors_occurred.append(f"Download {download_filename}")
                overall_success = False
        
        # Prossegue somente se o download foi OK ou o arquivo já existia
        if overall_success and os.path.isfile(downloaded_7z_file_path):
            # Pasta temporária para onde a pasta raiz do .7z será extraída
            temp_extraction_point = os.path.join(persistent_downloads_dir, "_temp_GEO_EXTRACTION_POINT")
            # Nome da pasta raiz DENTRO do arquivo .7z que queremos processar
            archive_internal_root_folder_name = "aCisDsec_Geodata" 
            # Caminho para a pasta aCisDsec_Geodata DEPOIS de extraída para temp_extraction_point
            extracted_archive_root_path = os.path.join(temp_extraction_point, archive_internal_root_folder_name)

            # ETAPA 0.B: Descompressão da pasta específica 'aCisDsec_Geodata'
            self.append_to_manager_console_from_thread(f"\nDescomprimindo '{archive_internal_root_folder_name}' de '{download_filename}'...\n")
            seven_zip_exe_path = os.path.join(self.base_dir, "Tools", "7za.exe")

            if not os.path.isfile(seven_zip_exe_path):
                self.append_to_manager_console_from_thread(f"ERRO: '{seven_zip_exe_path}' não encontrado.\n")
                errors_occurred.append("7za.exe não encontrado")
                overall_success = False
            else:
                try:
                    if os.path.isdir(temp_extraction_point): shutil.rmtree(temp_extraction_point)
                    os.makedirs(temp_extraction_point, exist_ok=True)
                    
                    # Comando para extrair APENAS a pasta "aCisDsec_Geodata" (e seu conteúdo) para temp_extraction_point
                    # O 7zip criará a pasta "aCisDsec_Geodata" dentro de temp_extraction_point
                    decompress_command = [
                        seven_zip_exe_path, "x", downloaded_7z_file_path,
                        "-r", # Recurso para subdiretórios
                        f"-o{temp_extraction_point}", # Diretório de SAÍDA para o 7zip
                        archive_internal_root_folder_name, # O que extrair DE DENTRO do .7z
                        "-y"  # Sim para todas as perguntas
                    ]
                    # O CWD pode ser o diretório do 7zip ou self.base_dir
                    decompress_ok = self._run_command_and_stream_output(decompress_command, os.path.dirname(seven_zip_exe_path)) 
                    
                    if not decompress_ok:
                        self.append_to_manager_console_from_thread(f"ERRO: Falha ao extrair '{archive_internal_root_folder_name}'.\n")
                        errors_occurred.append(f"Descompressão de {archive_internal_root_folder_name}")
                        overall_success = False
                    else:
                        self.append_to_manager_console_from_thread(f"Pasta '{archive_internal_root_folder_name}' extraída para '{temp_extraction_point}'.\n")
                except Exception as e_decompress:
                    self.append_to_manager_console_from_thread(f"ERRO durante a descompressão: {e_decompress}\n")
                    errors_occurred.append(f"Descompressão: {e_decompress}")
                    overall_success = False

            # ETAPA 0.C: Cópia do CONTEÚDO de 'aCisDsec_Geodata' para o destino final
            if overall_success:
                final_destination_for_contents = os.path.join(target_root_dir, "gameserver", "data")
                self.append_to_manager_console_from_thread(f"\nCopiando conteúdo de '{extracted_archive_root_path}' para '{final_destination_for_contents}'...\n")

                if not os.path.isdir(extracted_archive_root_path):
                    self.append_to_manager_console_from_thread(f"ERRO: Caminho do conteúdo extraído '{extracted_archive_root_path}' não encontrado!\n")
                    errors_occurred.append("Conteúdo extraído não encontrado")
                    overall_success = False
                else:
                    try:
                        os.makedirs(final_destination_for_contents, exist_ok=True)
                        
                        # Itera sobre os itens DENTRO de extracted_archive_root_path (ex: geodata, crests)
                        for item_name in os.listdir(extracted_archive_root_path):
                            src_item_path = os.path.join(extracted_archive_root_path, item_name)
                            dst_item_path = os.path.join(final_destination_for_contents, item_name) # Ex: .../data/geodata

                            self.append_to_manager_console_from_thread(f"  Processando item: '{item_name}' de '{src_item_path}' para '{dst_item_path}'\n")
                            if os.path.exists(dst_item_path):
                                self.append_to_manager_console_from_thread(f"    Destino '{dst_item_path}' já existe. Removendo antes de copiar...\n")
                                if os.path.isdir(dst_item_path):
                                    shutil.rmtree(dst_item_path)
                                else:
                                    os.remove(dst_item_path)
                            
                            if os.path.isdir(src_item_path):
                                shutil.copytree(src_item_path, dst_item_path)
                            else: # É um arquivo
                                shutil.copy2(src_item_path, dst_item_path)
                            self.append_to_manager_console_from_thread(f"    '{item_name}' copiado com sucesso.\n")
                    except Exception as e_copy_final:
                        self.append_to_manager_console_from_thread(f"  ERRO ao copiar conteúdo para o destino final: {e_copy_final}\n")
                        errors_occurred.append(f"Cópia final Geo/Crests: {e_copy_final}")
                        overall_success = False
            
            # ETAPA 0.D: Limpeza da pasta de extração temporária (temp_extraction_point)
            if os.path.isdir(temp_extraction_point):
                self.append_to_manager_console_from_thread(f"Limpando pasta de extração temporária '{temp_extraction_point}'...\n")
                try:
                    # (Sua lógica de limpeza com retries pode ser usada aqui)
                    shutil.rmtree(temp_extraction_point)
                    self.append_to_manager_console_from_thread("Limpeza de temporários da Etapa 0 concluída.\n")
                except Exception as e_clean:
                    self.append_to_manager_console_from_thread(f"AVISO: Falha ao limpar pasta de extração temporária '{temp_extraction_point}': {e_clean}\n")
        
        if not overall_success:
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO na Etapa 0 (Download/Descompressão/Cópia GeoData/Crests). As etapas seguintes podem ser afetadas.\n")
        else:
            self.append_to_manager_console_from_thread(f"--- Etapa 0: Processamento do pacote GeoData/Crests concluído. ---\n")


        # --- ETAPA 1. Copiar Arquivos do Datapack ---
        if overall_success: # Só executa se a Etapa 0 foi bem-sucedida (ou se você não abortou acima)
            self.append_to_manager_console_from_thread(f"\n--- 1. Copiando arquivos do Datapack de '{datapack_source_base}' ---\n")
            # (Sua lógica detalhada de cópia do datapack aqui, como antes)
            # ... (lembre-se de atualizar overall_success e errors_occurred se houver falhas aqui)
            if not os.path.isdir(datapack_source_base):
                self.append_to_manager_console_from_thread(f"AVISO: Diretório de origem do Datapack não encontrado: {datapack_source_base}. Pulando.\n")
            else:
                # ... (código de cópia do datapack) ...
                pass # Substitua pelo seu código de cópia do datapack
            self.append_to_manager_console_from_thread("Etapa 1 (Datapack) concluída (placeholder).\n") # Mensagem de placeholder
        else:
            self.append_to_manager_console_from_thread(f"\n--- Etapa 1: Cópia do Datapack pulada devido a falha crítica anterior. ---\n")


        # --- ETAPA 2. Copiar Arquivos do GameServer (dist) ---
        if overall_success: # Só executa se as etapas anteriores foram bem-sucedidas
            self.append_to_manager_console_from_thread(f"\n--- 2. Copiando arquivos do GameServer (dist) de '{gameserver_dist_source_base}' ---\n")
            # (Sua lógica detalhada de cópia do gameserver dist aqui, como antes)
            # ... (lembre-se de atualizar overall_success e errors_occurred se houver falhas aqui)
            if not os.path.isdir(gameserver_dist_source_base):
                self.append_to_manager_console_from_thread(f"AVISO: Diretório de origem do GameServer (dist) não encontrado: {gameserver_dist_source_base}. Pulando.\n")
            else:
                # ... (código de cópia do gameserver dist) ...
                pass # Substitua pelo seu código de cópia do gameserver dist
            self.append_to_manager_console_from_thread("Etapa 2 (GameServer dist) concluída (placeholder).\n") # Mensagem de placeholder
        else:
            self.append_to_manager_console_from_thread(f"\n--- Etapa 2: Cópia do GameServer (dist) pulada devido a falhas anteriores. ---\n")

        # Finalização
        final_message_text = ""
        if overall_success and not errors_occurred:
            final_message_text = "Preparação da inicialização (download e todas as cópias) concluída com sucesso!"
            self.append_to_manager_console_from_thread(f"\n{final_message_text}\nDiretório final: '{target_root_dir}'\n")
        else:
            error_details = "; ".join(errors_occurred) if errors_occurred else "Verifique o console para detalhes."
            final_message_text = f"Preparação da inicialização concluída com problemas. Detalhes: {error_details}"
            self.append_to_manager_console_from_thread(f"\n{final_message_text}\n")
        
        self.after(0, lambda: self._preparation_finished(overall_success and not errors_occurred, final_message_text))


        # --- ETAPA 1. Copiar Arquivos do Datapack ---
        # Esta etapa e a seguinte seriam executadas APÓS o download da Etapa 0.
        # A lógica de cópia aqui permanece a mesma que você já tinha,
        # mas agora ela ocorre após a Etapa 0 ter sido concluída.
        if overall_success: # Prossegue apenas se o download (que era a única parte crítica da Etapa 0 agora) foi OK
            self.append_to_manager_console_from_thread(f"\n--- 1. Copiando arquivos do Datapack de '{datapack_source_base}' ---\n")
            if not os.path.isdir(datapack_source_base):
                self.append_to_manager_console_from_thread(f"AVISO: Diretório de origem do Datapack não encontrado: {datapack_source_base}. Pulando esta etapa.\n")
                # Você pode definir overall_success = False aqui se esta etapa for obrigatória
            else:
                try:
                    # ... (sua lógica detalhada de cópia do datapack aqui, como no exemplo anterior) ...
                    # Exemplo simplificado para manter o foco:
                    for item_name in os.listdir(datapack_source_base):
                        src_item = os.path.join(datapack_source_base, item_name)
                        dst_item = os.path.join(target_root_dir, item_name)
                        if item_name == "gameserver" and os.path.isdir(src_item) and target_existed_before:
                             # Lógica especial para gameserver/data
                            self.append_to_manager_console_from_thread(f"  Processando pasta '{item_name}' (com exceção para 'data')...\n")
                            os.makedirs(dst_item, exist_ok=True) 
                            for sub_item_name in os.listdir(src_item):
                                src_sub_item = os.path.join(src_item, sub_item_name)
                                dst_sub_item = os.path.join(dst_item, sub_item_name)
                                if sub_item_name == "data" and os.path.isdir(src_sub_item):
                                    self.append_to_manager_console_from_thread(f"    Pulando subpasta: '{src_sub_item}' (regra: não sobrescrever gameserver/data se destino existia).\n")
                                    continue 
                                if os.path.isdir(src_sub_item): shutil.copytree(src_sub_item, dst_sub_item, dirs_exist_ok=True)
                                else: shutil.copy2(src_sub_item, dst_sub_item)
                        elif os.path.isdir(src_item): shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                        else: shutil.copy2(src_item, dst_item)
                    self.append_to_manager_console_from_thread("Cópia do Datapack concluída.\n")
                except Exception as e:
                    self.append_to_manager_console_from_thread(f"ERRO durante a cópia do Datapack: {e}\n")
                    errors_occurred.append(f"Datapack: {e}")
                    overall_success = False
        else:
            self.append_to_manager_console_from_thread(f"\n--- Etapa 1: Cópia do Datapack pulada devido a falha na Etapa 0. ---\n")


        # --- ETAPA 2. Copiar Arquivos do GameServer (dist) ---
        if overall_success: # Prossegue apenas se as etapas anteriores foram OK
            self.append_to_manager_console_from_thread(f"\n--- 2. Copiando arquivos do GameServer (dist) de '{gameserver_dist_source_base}' ---\n")
            if not os.path.isdir(gameserver_dist_source_base):
                self.append_to_manager_console_from_thread(f"AVISO: Diretório de origem do GameServer (dist) não encontrado: {gameserver_dist_source_base}. Pulando esta etapa.\n")
                # Você pode definir overall_success = False aqui se esta etapa for obrigatória
            else:
                try:
                    # ... (sua lógica detalhada de cópia do gameserver dist aqui, como no exemplo anterior) ...
                    # Exemplo simplificado para manter o foco:
                    folders_to_skip_if_dest_exists = {"login": ["config"], "gameserver": ["config"]}
                    for item_name in os.listdir(gameserver_dist_source_base):
                        src_item_path = os.path.join(gameserver_dist_source_base, item_name)
                        dst_item_path = os.path.join(target_root_dir, item_name)
                        if os.path.isdir(src_item_path) and item_name in folders_to_skip_if_dest_exists:
                            os.makedirs(dst_item_path, exist_ok=True)
                            subfolders_to_skip_for_this_item = folders_to_skip_if_dest_exists[item_name]
                            for sub_item_name in os.listdir(src_item_path):
                                src_sub_item_path = os.path.join(src_item_path, sub_item_name)
                                dst_sub_item_path = os.path.join(dst_item_path, sub_item_name)
                                if sub_item_name in subfolders_to_skip_for_this_item and os.path.isdir(src_sub_item_path) and os.path.exists(dst_sub_item_path):
                                    self.append_to_manager_console_from_thread(f"    Pulando subpasta: '{src_sub_item_path}' (regra {item_name}/{sub_item_name} e destino existe).\n")
                                    continue
                                if os.path.isdir(src_sub_item_path): shutil.copytree(src_sub_item_path, dst_sub_item_path, dirs_exist_ok=True)
                                else: shutil.copy2(src_sub_item_path, dst_sub_item_path)
                        elif os.path.isdir(src_item_path): shutil.copytree(src_item_path, dst_item_path, dirs_exist_ok=True)
                        else: shutil.copy2(src_item_path, dst_item_path)
                    self.append_to_manager_console_from_thread("Cópia do GameServer (dist) concluída.\n")
                except Exception as e:
                    self.append_to_manager_console_from_thread(f"ERRO durante a cópia do GameServer (dist): {e}\n")
                    errors_occurred.append(f"GameServer (dist): {e}")
                    overall_success = False
        else:
            self.append_to_manager_console_from_thread(f"\n--- Etapa 2: Cópia do GameServer (dist) pulada devido a falhas anteriores. ---\n")


        # Finalização
        final_message_text = ""
        if overall_success and not errors_occurred:
            final_message_text = "Preparação da inicialização (download e cópias) concluída com sucesso!"
            self.append_to_manager_console_from_thread(f"\n{final_message_text}\nDiretório final: '{target_root_dir}'\n")
        else:
            error_details = "; ".join(errors_occurred) if errors_occurred else "Verifique o console."
            final_message_text = f"Preparação da inicialização concluída com problemas. Detalhes: {error_details}"
            self.append_to_manager_console_from_thread(f"\n{final_message_text}\n")
        
        self.after(0, lambda: self._preparation_finished(overall_success, final_message_text))


        # --- 1. Copiar Arquivos do Datapack ---
        # (Seu código da Etapa 1 aqui - como na resposta anterior)
        # ...
        if overall_success: # Só prossegue se a Etapa 0 não teve falha crítica (se você não retornou acima)
            self.append_to_manager_console_from_thread(f"\n--- 1. Copiando arquivos do Datapack de '{datapack_source_base}' ---\n")
            # ... (lógica de cópia do datapack) ...
        # ... (resto do método como antes, atualizando overall_success e errors_occurred) ...

        # --- 2. Copiar Arquivos do GameServer (dist) ---
        if overall_success: # Só prossegue se as etapas anteriores não tiveram falha crítica
            self.append_to_manager_console_from_thread(f"\n--- 2. Copiando arquivos do GameServer (dist) de '{gameserver_dist_source_base}' ---\n")
            # ... (lógica de cópia do gameserver dist) ...

        # Finalização (como antes)
        if overall_success and not errors_occurred:
            msg = "Preparação da inicialização concluída com sucesso!"
            self.append_to_manager_console_from_thread(f"\n{msg}\nDiretório final: '{target_root_dir}'\n")
            self.after(0, lambda: self._preparation_finished(True, msg))
        else:
            error_details = "; ".join(errors_occurred) if errors_occurred else "Verifique o console."
            msg = f"Preparação da inicialização concluída com problemas. Detalhes: {error_details}"
            self.append_to_manager_console_from_thread(f"\n{msg}\n")
            self.after(0, lambda: self._preparation_finished(False, msg))
        """
        Executa a cópia e preparação dos arquivos em uma thread separada.
        """
        # !!! IMPORTANTE: AJUSTE ESTE CAMINHO SE NECESSÁRIO !!!
        # Deve ser o mesmo caminho raiz do projeto usado na compilação.
        project_source_dir = os.path.join(self.base_dir, "aCisDsec_project") 
        
        compiled_server_dir_name = "Servidor Compilado"
        target_root_dir = os.path.join(project_source_dir, compiled_server_dir_name)

        datapack_source_base = os.path.join(project_source_dir, "aCis_datapack", "build")
        gameserver_dist_source_base = os.path.join(project_source_dir, "aCis_gameserver", "build", "dist")

        self.append_to_manager_console_from_thread(f"\n--- Iniciando Preparação para Inicialização ---\n")
        self.append_to_manager_console_from_thread(f"Diretório do projeto fonte: {project_source_dir}\n")
        self.append_to_manager_console_from_thread(f"Diretório de destino final: {target_root_dir}\n")

        overall_success = True
        errors_occurred = []

        # Verifica se o diretório do projeto fonte existe
        if not os.path.isdir(project_source_dir):
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO: Diretório do projeto fonte '{project_source_dir}' não encontrado!\n")
            self.after(0, lambda: self._preparation_finished(False, "Diretório do projeto fonte não encontrado."))
            return

        target_existed_before = os.path.isdir(target_root_dir)
        try:
            os.makedirs(target_root_dir, exist_ok=True)
            self.append_to_manager_console_from_thread(f"Diretório de destino '{target_root_dir}' criado/verificado.\n")
        except Exception as e:
            self.append_to_manager_console_from_thread(f"ERRO CRÍTICO ao criar diretório de destino '{target_root_dir}': {e}\n")
            self.after(0, lambda: self._preparation_finished(False, "Falha ao criar diretório de destino."))
            return

        # --- 1. Copiar Arquivos do Datapack ---
        self.append_to_manager_console_from_thread(f"\n--- 1. Copiando arquivos do Datapack de '{datapack_source_base}' ---\n")
        if not os.path.isdir(datapack_source_base):
            self.append_to_manager_console_from_thread(f"AVISO: Diretório de origem do Datapack não encontrado: {datapack_source_base}. Pulando esta etapa.\n")
            # overall_success = False # Pode ser um aviso em vez de falha total
        else:
            try:
                for item_name in os.listdir(datapack_source_base):
                    src_item = os.path.join(datapack_source_base, item_name)
                    dst_item = os.path.join(target_root_dir, item_name)

                    if item_name == "gameserver" and os.path.isdir(src_item) and target_existed_before:
                        self.append_to_manager_console_from_thread(f"  Processando pasta '{item_name}' (com exceção para 'data')...\n")
                        os.makedirs(dst_item, exist_ok=True) 
                        for sub_item_name in os.listdir(src_item):
                            src_sub_item = os.path.join(src_item, sub_item_name)
                            dst_sub_item = os.path.join(dst_item, sub_item_name)
                            if sub_item_name == "data" and os.path.isdir(src_sub_item):
                                self.append_to_manager_console_from_thread(f"    Pulando subpasta: '{src_sub_item}' (regra: não sobrescrever gameserver/data se destino existia).\n")
                                continue 
                            
                            if os.path.isdir(src_sub_item):
                                shutil.copytree(src_sub_item, dst_sub_item, dirs_exist_ok=True)
                            else:
                                shutil.copy2(src_sub_item, dst_sub_item)
                        self.append_to_manager_console_from_thread(f"  Conteúdo de '{item_name}' (exceto 'data') copiado.\n")
                    elif os.path.isdir(src_item):
                        self.append_to_manager_console_from_thread(f"  Copiando pasta: {src_item} para {dst_item}\n")
                        shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                    else: # É um arquivo
                        self.append_to_manager_console_from_thread(f"  Copiando arquivo: {src_item} para {dst_item}\n")
                        shutil.copy2(src_item, dst_item)
                self.append_to_manager_console_from_thread("Cópia do Datapack concluída.\n")
            except Exception as e:
                self.append_to_manager_console_from_thread(f"ERRO durante a cópia do Datapack: {e}\n")
                errors_occurred.append(f"Datapack: {e}")
                overall_success = False

        # --- 2. Copiar Arquivos do GameServer (dist) ---
        self.append_to_manager_console_from_thread(f"\n--- 2. Copiando arquivos do GameServer (dist) de '{gameserver_dist_source_base}' ---\n")
        if not os.path.isdir(gameserver_dist_source_base):
            self.append_to_manager_console_from_thread(f"AVISO: Diretório de origem do GameServer (dist) não encontrado: {gameserver_dist_source_base}. Pulando esta etapa.\n")
            # overall_success = False # Pode ser um aviso
        else:
            try:
                # Pastas dentro de gameserver_dist_source_base/login ou /gameserver que não devem ser sobrescritas se já existirem no destino
                folders_to_skip_if_dest_exists = {
                    "login": ["config"],
                    "gameserver": ["config"]
                }

                for item_name in os.listdir(gameserver_dist_source_base): # Ex: item_name pode ser "login", "gameserver", etc.
                    src_item_path = os.path.join(gameserver_dist_source_base, item_name)
                    dst_item_path = os.path.join(target_root_dir, item_name)

                    if os.path.isdir(src_item_path) and item_name in folders_to_skip_if_dest_exists:
                        self.append_to_manager_console_from_thread(f"  Processando pasta '{item_name}' (com exceções para subpastas '{', '.join(folders_to_skip_if_dest_exists[item_name])}')...\n")
                        os.makedirs(dst_item_path, exist_ok=True) # Garante que a pasta de nível superior exista no destino
                        
                        subfolders_to_skip_for_this_item = folders_to_skip_if_dest_exists[item_name]
                        for sub_item_name in os.listdir(src_item_path): # Ex: sub_item_name pode ser "config", "libs", etc.
                            src_sub_item_path = os.path.join(src_item_path, sub_item_name)
                            dst_sub_item_path = os.path.join(dst_item_path, sub_item_name)

                            # Verifica se esta subpasta específica deve ser pulada e se ela já existe no destino
                            if sub_item_name in subfolders_to_skip_for_this_item and os.path.isdir(src_sub_item_path) and os.path.exists(dst_sub_item_path):
                                self.append_to_manager_console_from_thread(f"    Pulando subpasta: '{src_sub_item_path}' (regra: não sobrescrever {item_name}/{sub_item_name} se destino existe).\n")
                                continue
                            
                            if os.path.isdir(src_sub_item_path):
                                shutil.copytree(src_sub_item_path, dst_sub_item_path, dirs_exist_ok=True)
                            else:
                                shutil.copy2(src_sub_item_path, dst_sub_item_path)
                        self.append_to_manager_console_from_thread(f"  Conteúdo de '{item_name}' (com exceções) copiado.\n")
                    elif os.path.isdir(src_item_path): 
                        self.append_to_manager_console_from_thread(f"  Copiando pasta: {src_item_path} para {dst_item_path}\n")
                        shutil.copytree(src_item_path, dst_item_path, dirs_exist_ok=True)
                    else: 
                        self.append_to_manager_console_from_thread(f"  Copiando arquivo: {src_item_path} para {dst_item_path}\n")
                        shutil.copy2(src_item_path, dst_item_path)
                self.append_to_manager_console_from_thread("Cópia do GameServer (dist) concluída.\n")
            except Exception as e:
                self.append_to_manager_console_from_thread(f"ERRO durante a cópia do GameServer (dist): {e}\n")
                errors_occurred.append(f"GameServer (dist): {e}")
                overall_success = False

        # Finalização
        if overall_success and not errors_occurred:
            msg = "Preparação da inicialização concluída com sucesso!"
            self.append_to_manager_console_from_thread(f"\n{msg}\nDiretório final: '{target_root_dir}'\n")
            self.after(0, lambda: self._preparation_finished(True, msg))
        else:
            error_details = "; ".join(errors_occurred)
            msg = f"Preparação da inicialização concluída com erros. Detalhes: {error_details}"
            if not errors_occurred and not overall_success: # Se overall_success foi setado para False por outros motivos
                 msg = "Preparação da inicialização concluída com problemas. Verifique o console."

            self.append_to_manager_console_from_thread(f"\n{msg}\n")
            self.after(0, lambda: self._preparation_finished(False, msg))
            
    def _preparation_finished(self, success, message):
        """ Chamado ao final do processo de preparação para atualizar a UI. """
        if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
            try:
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.stop()
                self.loading_window.grab_release()
                self.loading_window.destroy()
            except tk.TclError:
                pass
            finally:
                self.loading_window = None
                if hasattr(self, 'progress_bar'):
                    del self.progress_bar

        self.prepare_init_button.config(state=tk.NORMAL) # Reabilita o botão
        
        if success:
            messagebox.showinfo("Preparação para Inicialização", message)
        else:
            messagebox.showerror("Preparação para Inicialização", f"Falha no processo: {message}\nVerifique o console para mais detalhes.")
        
        self.lift()
        self.focus_force()
    
    def _download_gdrive_file(self, gdrive_url, destination_path):
        """
        Baixa um arquivo do Google Drive, lidando com a página de confirmação de arquivos grandes.
        Requer a biblioteca 'requests'.
        gdrive_url: URL de compartilhamento do Google Drive.
        destination_path: Caminho completo onde salvar o arquivo.
        Retorna True se o download for bem-sucedido, False caso contrário.
        """
        self.append_to_manager_console_from_thread(f"Iniciando download de: {gdrive_url}\nPara: {destination_path}\n")
        
        file_id = None
        try:
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', gdrive_url)
            if match:
                file_id = match.group(1)
        except Exception:
            pass
            
        if not file_id:
            self.append_to_manager_console_from_thread("ERRO: ID do arquivo do Google Drive não pôde ser extraído da URL fornecida.\n")
            return False

        initial_download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        try:
            import requests
        except ImportError:
            self.append_to_manager_console_from_thread(
                "ERRO CRÍTICO: A biblioteca 'requests' é necessária para esta funcionalidade de download do Google Drive mas não está instalada.\n"
                "Por favor, permita a instalação quando o programa iniciar ou instale manualmente ('pip install requests').\n"
            )
            return False

        try:
            session = requests.Session() # Usar uma sessão para persistir cookies se necessário
            self.append_to_manager_console_from_thread(f"Tentando baixar (com 'requests') de: {initial_download_url}\n")
            
            # Primeira requisição para obter a página de aviso ou o arquivo diretamente
            response1 = session.get(initial_download_url, stream=True, timeout=20) # Timeout menor para a primeira requisição
            response1.raise_for_status()

            # Verifica se é a página de aviso HTML
            content_type1 = response1.headers.get('Content-Type', '').lower()
            is_html_warning_page = 'text/html' in content_type1
            
            actual_file_response = response1

            if is_html_warning_page:
                html_content = response1.text # Lê o conteúdo da página de aviso
                if "Virus scan warning" in html_content or "uc-download-link" in html_content : # Confirma que é a página de aviso
                    self.append_to_manager_console_from_thread("Página de aviso do Google Drive detectada. Extraindo informações do formulário...\n")

                    form_action_match = re.search(r'<form.*?id="download-form".*?action="([^"]+)"', html_content, re.IGNORECASE)
                    if not form_action_match:
                        self.append_to_manager_console_from_thread("ERRO: Não foi possível encontrar a URL 'action' do formulário de download na página de aviso.\n")
                        return False
                    
                    confirm_url = form_action_match.group(1) # Ex: https://drive.usercontent.google.com/download

                    form_params = {}
                    hidden_inputs = re.findall(r'<input.*?type="hidden".*?name="([^"]+)".*?value="([^"]*)"', html_content, re.IGNORECASE)
                    
                    if not hidden_inputs:
                        self.append_to_manager_console_from_thread("ERRO: Não foi possível encontrar os campos ocultos (hidden inputs) do formulário de download.\n")
                        return False
                    
                    for name, value in hidden_inputs:
                        form_params[name] = value
                    
                    self.append_to_manager_console_from_thread(f"Parâmetros de confirmação extraídos: {form_params}\n")
                    self.append_to_manager_console_from_thread(f"Enviando requisição de download final para: {confirm_url}\n")
                    
                    # Segunda requisição - o download real
                    actual_file_response = session.get(confirm_url, params=form_params, stream=True, timeout=3600) # Timeout maior para download
                    actual_file_response.raise_for_status()
                else:
                    # É HTML mas não a página de aviso esperada
                    self.append_to_manager_console_from_thread("ERRO: Recebido HTML inesperado do Google Drive. Não é a página de aviso conhecida.\n")
                    return False

            # Neste ponto, actual_file_response deve ser o stream do arquivo real
            final_content_type = actual_file_response.headers.get('Content-Type', '').lower()
            if 'text/html' in final_content_type:
                 self.append_to_manager_console_from_thread("ERRO: Download final ainda resultou em uma página HTML. O mecanismo de download do Google Drive pode ter mudado.\n")
                 return False

            self.append_to_manager_console_from_thread("Iniciando gravação do arquivo...\n")
            total_downloaded_bytes = 0
            with open(destination_path, 'wb') as f:
                for chunk in actual_file_response.iter_content(chunk_size=81920): # Chunks de 80KB
                    if chunk:
                        f.write(chunk)
                        total_downloaded_bytes += len(chunk)
            
            downloaded_mb = total_downloaded_bytes / (1024 * 1024)
            self.append_to_manager_console_from_thread(f"Download concluído. Total baixado: {downloaded_mb:.2f} MB.\n")

            # Verificação simples do tamanho (aproximado de 529M que você mencionou)
            expected_min_size_mb = 500 
            if downloaded_mb < expected_min_size_mb:
                self.append_to_manager_console_from_thread(
                    f"AVISO: Tamanho do arquivo baixado ({downloaded_mb:.2f}MB) é menor que o esperado ({expected_min_size_mb}MB+).\n"
                    "O download pode estar incompleto ou o arquivo no Drive é menor que o previsto."
                )
                # Você pode decidir se isso é um erro fatal: return False
            else:
                self.append_to_manager_console_from_thread("Tamanho do arquivo parece consistente.\n")
            
            return True
            
        except requests.exceptions.RequestException as e_req:
            self.append_to_manager_console_from_thread(f"ERRO DE REDE (requests) durante o download: {e_req}\n")
        except Exception as e_gen:
            self.append_to_manager_console_from_thread(f"ERRO GERAL durante o download: {e_gen}\n")
        
        # Limpeza em caso de erro
        if os.path.exists(destination_path):
            try:
                # Remove apenas se for o arquivo HTML pequeno
                if os.path.getsize(destination_path) < 1 * 1024 * 1024: # Se menor que 1MB, provavelmente não é o arquivo certo
                    os.remove(destination_path)
                    self.append_to_manager_console_from_thread(f"Arquivo parcial/incorreto '{destination_path}' removido devido a erro.\n")
            except Exception: 
                pass # Falha ao remover não é crítico aqui
        return False
    
        
        
    def compile_project_git(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.append_to_manager_console(f"[{timestamp}] Comando 'Compilar projeto (git)' acionado.\n")

        # --- ETAPA PRELIMINAR: VERIFICAR E CONFIGURAR JAVA_HOME ---
        self.append_to_manager_console("Verificando configuração do JAVA_HOME...\n")
        current_java_home_env = os.environ.get("JAVA_HOME")
        resolved_java_home_for_ant = current_java_home_env
        
        # Valida o JAVA_HOME do ambiente (se existir)
        is_current_java_home_valid = False
        if current_java_home_env:
            # Reutiliza a lógica de validação do diálogo
            temp_dialog_for_validation = JavaHomeDialog(self, current_java_home=current_java_home_env)
            is_current_java_home_valid = temp_dialog_for_validation._is_valid_jdk_path(current_java_home_env)
            temp_dialog_for_validation.destroy() # Destroi o diálogo temporário usado só para validação

        if current_java_home_env and is_current_java_home_valid:
            self.append_to_manager_console(f"INFO: JAVA_HOME encontrado no ambiente do sistema e parece válido: {current_java_home_env}\n")
            # Pergunta se o usuário quer usar este ou fornecer um novo
            use_system_java_home = messagebox.askyesno(
                "JAVA_HOME Encontrado",
                f"JAVA_HOME detectado no sistema:\n{current_java_home_env}\n\nEste parece ser um JDK válido. Deseja usá-lo para a compilação?",
                parent=self
            )
            if not use_system_java_home:
                resolved_java_home_for_ant = None # Força a abertura do diálogo de input
        else:
            if current_java_home_env: # Existia mas não era válido
                 self.append_to_manager_console(f"AVISO: JAVA_HOME do sistema ('{current_java_home_env}') parece ser inválido ou incompleto.\n")
            else: # Não existia
                 self.append_to_manager_console("INFO: JAVA_HOME não encontrado no ambiente do sistema.\n")
            resolved_java_home_for_ant = None # Força a abertura do diálogo

        if not resolved_java_home_for_ant: # Se não usamos o do sistema ou ele era inválido/ausente
            self.append_to_manager_console("Solicitando ao usuário para confirmar/fornecer o caminho do JAVA_HOME...\n")
            # O padrão C:\Program Files\Java\jdk-21 é passado para o diálogo
            java_home_dialog = JavaHomeDialog(self, current_java_home=current_java_home_env, default_jdk_path=r"C:\Program Files\Java\jdk-21")
            user_provided_java_home = java_home_dialog.result_path

            if user_provided_java_home:
                resolved_java_home_for_ant = user_provided_java_home
                self.append_to_manager_console(f"INFO: Usando JAVA_HOME fornecido/confirmado pelo usuário: {resolved_java_home_for_ant}\n")
            else:
                self.append_to_manager_console("ERRO: Caminho do JAVA_HOME não fornecido ou diálogo cancelado. Compilação abortada.\n")
                messagebox.showerror("JAVA_HOME Requerido", "A compilação não pode prosseguir sem um caminho válido para o JAVA_HOME (JDK).")
                return # Aborta a compilação

        # Se chegou aqui, resolved_java_home_for_ant contém um caminho válido para o JDK
        
        # Prossegue com a lógica de compilação existente
        self.compile_project_button.config(state=tk.DISABLED)
        self._show_loading_modal(title="Compilando", message="Compilando o projeto...\nGit Pull e Ant em execução.\nPor favor, aguarde.")
        
        # Passa o JAVA_HOME resolvido para a thread de compilação
        compilation_thread = threading.Thread(
            target=self._perform_compilation_thread, 
            args=(resolved_java_home_for_ant,), # Passa como argumento
            daemon=True
        )
        compilation_thread.start()
        
    def _compilation_finished(self, success, message):
        """ Chamado ao final do processo de compilação para atualizar a UI. """
        
        # Fecha a janela de loading modal, se existir
        if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
            try:
                if hasattr(self, 'progress_bar'): # Garante que progress_bar existe
                    self.progress_bar.stop() # Para a animação da barra
                self.loading_window.grab_release() # Libera o bloqueio modal
                self.loading_window.destroy()
            except tk.TclError:
                pass # Janela pode já ter sido destruída
            finally:
                self.loading_window = None # Limpa a referência
                if hasattr(self, 'progress_bar'):
                    del self.progress_bar # Limpa referência da barra

        self.compile_project_button.config(state=tk.NORMAL) # Reabilita o botão de compilação
        
        if success:
            messagebox.showinfo("Compilação do Projeto", message)
        else:
            messagebox.showerror("Compilação do Projeto", f"Falha no processo: {message}\nVerifique o console para mais detalhes.")
        
        # Traz a janela principal para frente novamente
        self.lift()
        self.focus_force()
        
        
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
            
    def _show_loading_modal(self, title="Processando...", message="Por favor, aguarde..."):
        """ Cria e exibe uma janela Toplevel modal com uma barra de progresso indeterminada. """
        if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
            # Se já existir uma, feche-a para evitar múltiplas janelas de loading
            try:
                self.loading_window.destroy()
            except tk.TclError:
                pass # Pode já ter sido destruída

        self.loading_window = tk.Toplevel(self)
        self.loading_window.title(title)
        self.loading_window.resizable(False, False)  # Impede redimensionamento
        self.loading_window.transient(self)      # Mantém sobre a janela principal
        
        # Define um tamanho fixo para a janela modal
        modal_width = 320
        modal_height = 130

        # Calcula a posição para centralizar na janela principal
        # Garante que a janela principal já tenha suas dimensões definidas
        self.update_idletasks() 
        main_win_x = self.winfo_x()
        main_win_y = self.winfo_y()
        main_win_width = self.winfo_width()
        main_win_height = self.winfo_height()

        position_x = main_win_x + (main_win_width // 2) - (modal_width // 2)
        position_y = main_win_y + (main_win_height // 2) - (modal_height // 2)
        
        self.loading_window.geometry(f"{modal_width}x{modal_height}+{position_x}+{position_y}")

        # Impede que o usuário feche a janela de loading manualmente pelo botão 'X'
        self.loading_window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Estilo para os widgets ttk (opcional, mas pode melhorar a aparência)
        style = ttk.Style(self.loading_window)
        # Tenta usar um tema que pode ser mais moderno, se disponível
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        elif 'vista' in available_themes and sys.platform == "win32":
            style.theme_use('vista')
        
        # Frame para organizar o conteúdo
        content_frame = ttk.Frame(self.loading_window, padding="10 10 10 10")
        content_frame.pack(expand=True, fill=tk.BOTH)

        loading_label = ttk.Label(content_frame, text=message, justify=tk.CENTER, font=("Arial", 10))
        loading_label.pack(pady=(10, 15))

        # Barra de progresso indeterminada
        self.progress_bar = ttk.Progressbar(content_frame, mode='indeterminate', length=modal_width - 60)
        self.progress_bar.pack(pady=5)
        self.progress_bar.start(15)  # Inicia a animação da barra (intervalo em ms)

        self.loading_window.grab_set()  # Torna a janela modal, bloqueando interações com a principal
        self.loading_window.focus_force() # Tenta focar na janela modal
        self.update_idletasks() # Garante que a janela seja desenhada
            

    def _perform_compilation_thread(self, resolved_java_home): # Novo argumento
        """
        Executa as etapas de clone/pull do Git e compilação com Ant (embutido) em uma thread separada.
        Usa o JAVA_HOME resolvido.
        """
        # ... (definição de project_source_dir, git_repo_url, git_branch como antes) ...
        project_source_dir = os.path.join(self.base_dir, "aCisDsec_project") 
        git_repo_url = "https://github.com/Dhousefe/aCisDsec.git"
        git_branch = "master" 

        self.append_to_manager_console_from_thread(f"\n--- Iniciando processo de compilação do projeto ---\n")
        self.append_to_manager_console_from_thread(f"Usando JAVA_HOME: {resolved_java_home}\n") # Log do JAVA_HOME a ser usado
        self.append_to_manager_console_from_thread(f"Diretório do projeto alvo: {project_source_dir}\n")
        # ...

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
        # --- ETAPA 2: CONFIGURAÇÃO E VERIFICAÇÃO DO ANT (DENTRO DO PROJETO GIT) ---
        self.append_to_manager_console_from_thread(f"\n--- Etapa 2: Configurando e verificando Ant (embutido no projeto Git) ---\n")
        ant_folder_name_in_project = "Ant"
        ant_home_path = os.path.join(project_source_dir, ant_folder_name_in_project) 
        ant_bin_path = os.path.join(ant_home_path, "bin")
        ant_executable_name = "ant.bat" if sys.platform == "win32" else "ant"
        ant_executable_full_path = os.path.join(ant_bin_path, ant_executable_name)

        self.append_to_manager_console_from_thread(f"Procurando Ant do projeto em: {ant_home_path}\n")

        if not (os.path.isdir(ant_home_path) and os.path.isfile(ant_executable_full_path)):
            self.append_to_manager_console_from_thread(f"ERRO: Ant do projeto não encontrado em '{ant_home_path}'.\n")
            self.after(0, lambda: self._compilation_finished(False, "Ant não encontrado dentro do projeto."))
            return
        
        # Cria um ambiente customizado para o Ant
        ant_env = os.environ.copy()
        ant_env["ANT_HOME"] = ant_home_path
        ant_env["PATH"] = ant_bin_path + os.pathsep + ant_env.get("PATH", "")
        ant_env["JAVA_HOME"] = resolved_java_home # *** USA O JAVA_HOME RESOLVIDO ***
        
        self.append_to_manager_console_from_thread(f"Verificando Ant do projeto com '{ant_executable_full_path} -version' (JAVA_HOME='{ant_env['JAVA_HOME']}')...\n")
        try:
            result = subprocess.run(
                [ant_executable_full_path, "-version"], capture_output=True, check=True, text=True,
                env=ant_env, # Passa o ambiente com JAVA_HOME e ANT_HOME
                encoding='oem' if sys.platform == "win32" else 'utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            first_line_version = result.stdout.splitlines()[0] if result.stdout.splitlines() else "N/A"
            self.append_to_manager_console_from_thread(f"INFO: Ant do projeto funcional. ({first_line_version})\n")
        except Exception as e:
            self.append_to_manager_console_from_thread(f"ERRO: Falha ao executar o Ant do projeto ('{ant_executable_full_path} -version'). Causa: {e}\nVerifique as configurações de ANT_HOME e JAVA_HOME e a integridade da pasta Ant.\n")
            self.after(0, lambda: self._compilation_finished(False, "Falha ao verificar Ant do projeto."))
            return
        # ...

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
            ant_compile_command_datapack = [ant_executable_full_path, "-v"]
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
            # Antes de compilar o gameserver
            ant_clean_command_gameserver = [ant_executable_full_path, "clean"]
            self.append_to_manager_console_from_thread(f"Executando 'ant clean' para GameServer...\n")
            self._run_command_and_stream_output(ant_clean_command_gameserver, gameserver_build_dir, custom_env=ant_env)

            # Depois o comando de compilação normal
            ant_compile_command_gameserver = [ant_executable_full_path, "-v"]
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
        
class MariaDBConfigDialog(tk.Toplevel):
    def __init__(self, parent, default_ip="localhost", default_user="root", db_name="aCisDsec"):
        super().__init__(parent)
        self.transient(parent) # Mantém sobre a janela principal
        self.title("Configurar Conexão MariaDB/MySQL")
        self.parent = parent
        self.result = None # Para armazenar os dados inseridos

        self.default_mysql_bin_path = r"C:\Program Files\MariaDB 10.5\bin" # Padrão

        frame = ttk.Frame(self, padding="10 10 10 10")
        frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text=f"Será criado/utilizado o banco de dados: '{db_name}'.").grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(frame, text="IP do Servidor MySQL/MariaDB:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ip_entry = ttk.Entry(frame, width=40)
        self.ip_entry.insert(0, default_ip)
        self.ip_entry.grid(row=1, column=1, pady=2, sticky=tk.EW)

        ttk.Label(frame, text="Usuário do MySQL/MariaDB:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.user_entry = ttk.Entry(frame, width=40)
        self.user_entry.insert(0, default_user)
        self.user_entry.grid(row=2, column=1, pady=2, sticky=tk.EW)

        ttk.Label(frame, text="Senha do Usuário:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.pass_entry = ttk.Entry(frame, width=40, show="*")
        self.pass_entry.grid(row=3, column=1, pady=2, sticky=tk.EW)
        
        ttk.Label(frame, text="Caminho para 'bin' do MySQL/MariaDB:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.mysql_bin_path_entry = ttk.Entry(frame, width=40)
        self.mysql_bin_path_entry.insert(0, self.default_mysql_bin_path)
        self.mysql_bin_path_entry.grid(row=4, column=1, pady=2, sticky=tk.EW)
        
        browse_button = ttk.Button(frame, text="Procurar...", command=self._browse_mysql_bin_path)
        browse_button.grid(row=4, column=2, padx=(5,0), pady=2)


        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10) # Alterado columnspan para 3

        self.ok_button = ttk.Button(button_frame, text="Iniciar Procedimento", command=self._on_ok)
        self.ok_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.grab_set() # Torna a janela modal
        self.protocol("WM_DELETE_WINDOW", self._on_cancel) # Lidar com fechamento pelo 'X'
        
        self.ip_entry.focus_set() # Foco no primeiro campo
        self.wait_window(self) # Espera até que esta janela seja fechada

    def _browse_mysql_bin_path(self):
        path = filedialog.askdirectory(initialdir=self.mysql_bin_path_entry.get() or self.default_mysql_bin_path,
                                        title="Selecione a pasta 'bin' do MariaDB/MySQL")
        if path:
            self.mysql_bin_path_entry.delete(0, tk.END)
            self.mysql_bin_path_entry.insert(0, path)

    def _on_ok(self, event=None):
        db_ip = self.ip_entry.get().strip()
        db_user = self.user_entry.get().strip()
        db_pass = self.pass_entry.get() # Senha pode ser vazia intencionalmente
        mysql_bin = self.mysql_bin_path_entry.get().strip()

        if not db_ip:
            messagebox.showerror("Entrada Inválida", "O IP do servidor não pode estar vazio.", parent=self)
            return
        if not db_user:
            messagebox.showerror("Entrada Inválida", "O usuário do banco de dados não pode estar vazio.", parent=self)
            return
        if not mysql_bin or not os.path.isdir(mysql_bin):
            messagebox.showerror("Entrada Inválida", "O caminho para a pasta 'bin' do MySQL/MariaDB é inválido ou não existe.", parent=self)
            return
        
        mysql_exe = "mysql.exe" if sys.platform == "win32" else "mysql"
        mysql_exe_path_full = os.path.join(mysql_bin, mysql_exe)
        if not os.path.isfile(mysql_exe_path_full):
            messagebox.showerror("Entrada Inválida", f"O executável '{mysql_exe}' não foi encontrado em '{mysql_bin}'.\nVerifique o caminho.", parent=self)
            return

        self.result = {
            "host": db_ip,
            "user": db_user,
            "password": db_pass,
            "db_name": "aCisDsec", # Fixo, conforme solicitado
            "mysql_exe_path": mysql_exe_path_full
        }
        self.destroy()

    def _on_cancel(self, event=None):
        self.result = None
        self.destroy()
        
        
class JavaHomeDialog(tk.Toplevel):
    def __init__(self, parent, current_java_home=None, default_jdk_path=r"C:\Program Files\Java\jdk-21"):
        super().__init__(parent)
        self.transient(parent)
        self.title("Configurar JAVA_HOME")
        self.parent = parent
        self.result_path = None  # Para armazenar o caminho confirmado

        # Define um caminho inicial para o Entry: o JAVA_HOME atual, o padrão, ou vazio
        initial_path_to_show = current_java_home or default_jdk_path or ""

        frame = ttk.Frame(self, padding="10 10 10 10")
        frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text="O Apache Ant requer o JAVA_HOME (caminho do JDK) para compilar o projeto.").grid(row=0, column=0, columnspan=3, pady=(0,10), sticky=tk.W)
        
        ttk.Label(frame, text="Caminho do JDK (JAVA_HOME):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.path_entry = ttk.Entry(frame, width=50)
        self.path_entry.insert(0, initial_path_to_show)
        self.path_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)

        browse_button = ttk.Button(frame, text="Procurar...", command=self._browse_jdk_path)
        browse_button.grid(row=1, column=2, padx=(5,0), pady=5)

        # Mensagem sobre o JAVA_HOME atual do sistema (se existir)
        if current_java_home:
            ttk.Label(frame, text=f"JAVA_HOME atual do sistema: {current_java_home}", wraplength=400).grid(row=2, column=0, columnspan=3, pady=(5,0), sticky=tk.W)
        else:
            ttk.Label(frame, text="JAVA_HOME não detectado no ambiente do sistema.", foreground="orange").grid(row=2, column=0, columnspan=3, pady=(5,0), sticky=tk.W)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(15,5))

        self.ok_button = ttk.Button(button_frame, text="Confirmar Caminho", command=self._on_confirm)
        self.ok_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancelar Compilação", command=self._on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.grab_set() # Modal
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.path_entry.focus_set()
        self.wait_window(self)

    def _browse_jdk_path(self):
        # Tenta usar o caminho no Entry como diretório inicial, ou o diretório pai do padrão
        initial_dir_browse = self.path_entry.get()
        if not os.path.isdir(initial_dir_browse): # Se não for um diretório válido
            initial_dir_browse = os.path.dirname(r"C:\Program Files\Java") # Um local comum
            if not os.path.isdir(initial_dir_browse): # Fallback
                 initial_dir_browse = "/"


        path = filedialog.askdirectory(initialdir=initial_dir_browse,
                                        title="Selecione o diretório raiz do JDK (ex: jdk-21)")
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def _is_valid_jdk_path(self, path_to_check):
        if not path_to_check or not os.path.isdir(path_to_check):
            return False
        # Verifica a existência de arquivos/pastas chave do JDK
        has_bin = os.path.isdir(os.path.join(path_to_check, "bin"))
        has_javac_win = os.path.isfile(os.path.join(path_to_check, "bin", "javac.exe"))
        has_javac_nix = os.path.isfile(os.path.join(path_to_check, "bin", "javac"))
        return has_bin and (has_javac_win or has_javac_nix)

    def _on_confirm(self, event=None):
        chosen_path = self.path_entry.get().strip()
        if not chosen_path:
            messagebox.showwarning("Caminho Vazio", "O caminho do JAVA_HOME não pode estar vazio.", parent=self)
            return
        
        if not self._is_valid_jdk_path(chosen_path):
            messagebox.showerror("Caminho Inválido", 
                                 f"O caminho '{chosen_path}' não parece ser um diretório JDK válido.\n"
                                 "Ele deve conter uma subpasta 'bin' com o compilador 'javac'.", parent=self)
            return

        self.result_path = chosen_path
        self.destroy()

    def _on_cancel(self, event=None):
        self.result_path = None # Indica cancelamento ou falha em obter um caminho válido
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

    
    
    # --- GARANTIR DISPONIBILIDADE DA BIBLIOTECA 'requests' ---
    print("Verificando a disponibilidade da biblioteca 'requests'...")
    # A função ensure_requests_library_installed() já imprime e mostra messageboxes.
    # O valor de retorno pode ser usado se você quiser tomar decisões adicionais,
    # mas a função _download_gdrive_file já tem um fallback.
    ensure_requests_library_installed() 
    print("Verificação de 'requests' concluída. Prosseguindo com a inicialização da aplicação...\n")
    
    # --- VERIFICAR DISPONIBILIDADE DO GIT ---
    git_available = ensure_git_is_available()
    if not git_available:
        print("AVISO: Git não está disponível. Funcionalidades que dependem do Git (como compilação de projeto) podem estar desabilitadas ou não funcionarão.\n")
    else:
        print("INFO: Git está disponível para uso.\n")
    
    # Código para melhorar a aparência no Windows (DPI awareness)
    # Código para melhorar a aparência no Windows (DPI awareness)
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1) 
        except Exception:
            pass 
            
    app = GameServerManager()
    
    # Passar o status do Git para a instância da app para que ela possa desabilitar o botão se necessário
    app.is_git_available = git_available 
    if not git_available and hasattr(app, 'compile_project_button'):
        # Tenta desabilitar o botão se já foi criado; idealmente, o botão verificaria essa flag ao ser clicado
         try:
            app.compile_project_button.config(state=tk.DISABLED)
            app.append_to_manager_console("AVISO: Botão 'Compilar projeto (git)' desabilitado pois Git não foi encontrado.\n")
         except tk.TclError: # Botão pode não existir ainda ou app não totalmente pronta
            pass
            
    app.mainloop()