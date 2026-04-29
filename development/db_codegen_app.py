#!/usr/bin/env python
"""
Interactive Database Code Generator Application

A multi-stage TUI application for generating code from database schemas.
"""
import os
import subprocess
import socket
import threading
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Label, RichLog, Checkbox, LoadingIndicator
from textual.binding import Binding
from textual.validation import ValidationResult, Validator


class ReplicaNameValidator(Validator):
    """Validator for replica name."""

    def validate(self, value: str) -> ValidationResult:
        """Validate that the replica name is not empty."""
        if not value or not value.strip():
            return self.failure("Replica name cannot be empty")
        return self.success()


class StageIndicator(Static):
    """Widget to display current stage progress."""

    def __init__(self, total_stages: int = 5):
        super().__init__()
        self.total_stages = total_stages
        self.current_stage = 1

    def set_stage(self, stage: int):
        """Update the current stage."""
        self.current_stage = stage
        self.update_display()

    def update_display(self):
        """Render the stage indicator."""
        stage_names = {
            1: "Source Database",
            2: "Proxy Connection",
            3: "Credentials",
            4: "Extract Schema",
            5: "Codegen"
        }

        stages = []
        for i in range(1, self.total_stages + 1):
            stage_label = f"{i}. {stage_names[i]}"
            if i < self.current_stage:
                stages.append(f"[green]✓ {stage_label}[/green]")
            elif i == self.current_stage:
                stages.append(f"[bold cyan]► {stage_label}[/bold cyan]")
            else:
                stages.append(f"[dim]○ {stage_label}[/dim]")

        self.update(" • ".join(stages))

    def on_mount(self):
        """Initialize display when mounted."""
        self.update_display()


class Stage1Screen(Container):
    """Stage 1: Get database replica name."""

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]Stage 1: Source Database[/bold]\n")
        yield Static("Please provide the name of the source database replica.\n")
        yield Label("Replica Name:")
        yield Input(
            placeholder="Enter replica name",
            value="arxiv-production-rep11",
            id="replica_name",
            validators=[ReplicaNameValidator()]
        )

        schema_file = Path("arxiv/db/arxiv_db_schema.sql")
        buttons = [Button("Continue", variant="primary", id="continue")]
        if schema_file.exists():
            buttons.append(Button("Skip to Stage 5 - Codegen", variant="success", id="skip_to_5"))
        buttons.append(Button("Quit", variant="error", id="quit"))

        yield Horizontal(*buttons)
        yield Static(id="error_message")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "skip_to_5":
            self.app_instance.schema_file = Path("arxiv/db/arxiv_db_schema.sql")
            self.app_instance.move_to_stage_5()
        elif event.button.id == "continue":
            replica_widget = self.query_one("#replica_name", Input)
            replica_name = replica_widget.value.strip() or "arxiv-production-rep11"

            if not replica_name:
                self.show_error("Please enter a replica name")
                return

            self.app_instance.replica_name = replica_name
            self.show_error(f"[green]✓ Replica name set: {replica_name}[/green]")
            self.app_instance.move_to_stage_2()

    def show_error(self, message: str):
        """Display an error or success message."""
        error_widget = self.query_one("#error_message", Static)
        error_widget.update(f"\n{message}")


class Stage2Screen(Container):
    """Stage 2: Start Cloud SQL Proxy."""

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]Stage 2: Proxy Connection[/bold]\n")
        yield Static("Configure and start the Cloud SQL Proxy to connect to the database.\n")

        yield Label("Proxy Port:")
        yield Input(value="2021", id="proxy_port")

        yield Horizontal(
            Button("Start Proxy", variant="primary", id="start_proxy"),
            Button("Back", variant="default", id="back"),
            Button("Quit", variant="error", id="quit"),
        )
        yield Static(id="status_message")
        yield RichLog(id="output_log", wrap=True, highlight=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "quit":
            self.app_instance.cleanup_proxy()
            self.app.exit()
        elif event.button.id == "back":
            self.app_instance.cleanup_proxy()
            self.app_instance.move_to_stage_1()
        elif event.button.id == "start_proxy":
            self.start_cloud_sql_proxy()
        elif event.button.id == "continue":
            self.app_instance.move_to_stage_3()

    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return False
            except OSError:
                return True

    def start_cloud_sql_proxy(self):
        """Start the Cloud SQL Proxy."""
        proxy_port = self.query_one("#proxy_port", Input).value
        replica_name = self.app_instance.replica_name

        if not proxy_port or not replica_name:
            self.show_status("[red]Error: Proxy port and replica name are required[/red]")
            return

        self.query_one("#start_proxy", Button).disabled = True
        self.show_status("[yellow]Checking proxy status...[/yellow]")

        log = self.query_one("#output_log", RichLog)
        log.clear()

        try:
            port_num = int(proxy_port)
        except ValueError:
            log.write(f"[red]✗ Invalid port number: {proxy_port}[/red]")
            self.show_status("[red]Invalid port number[/red]")
            self.query_one("#start_proxy", Button).disabled = False
            return

        if self.is_port_in_use(port_num):
            log.write(f"[yellow]Port {proxy_port} is already in use[/yellow]")
            log.write("[green]✓ Assuming Cloud SQL Proxy is already running[/green]")
            log.write(f"[green]Proxy appears to be running on 0.0.0.0:{proxy_port}[/green]")
            self.show_status("[green]✓ Proxy already running! Click Continue to proceed.[/green]")

            self.app_instance.proxy_port = proxy_port

            button_container = self.query_one(Horizontal)
            start_btn = self.query_one("#start_proxy", Button)
            start_btn.remove()
            button_container.mount(Button("Continue", variant="success", id="continue"), before=0)
            return

        proxy_cmd = [
            "/usr/local/bin/cloud-sql-proxy",
            "--address", "0.0.0.0",
            "--port", proxy_port,
            f"arxiv-production:us-central1:{replica_name}"
        ]

        log.write(f"[cyan]Executing:[/cyan] {' '.join(proxy_cmd)}")
        log.write(f"[cyan]Replica:[/cyan] {replica_name}")
        log.write(f"[cyan]Port:[/cyan] {proxy_port}")

        try:
            self.app_instance.proxy_process = subprocess.Popen(
                proxy_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            self.app_instance.proxy_port = proxy_port

            import time
            time.sleep(2)

            if self.app_instance.proxy_process.poll() is None:
                log.write(f"[green]✓ Cloud SQL Proxy started successfully (PID: {self.app_instance.proxy_process.pid})[/green]")
                log.write(f"[green]Proxy is running on 0.0.0.0:{proxy_port}[/green]")
                self.show_status("[green]✓ Proxy running! Click Continue to proceed.[/green]")

                button_container = self.query_one(Horizontal)
                start_btn = self.query_one("#start_proxy", Button)
                start_btn.remove()
                button_container.mount(Button("Continue", variant="success", id="continue"), before=0)
            else:
                log.write("[red]✗ Proxy process terminated unexpectedly[/red]")
                self.show_status("[red]Failed to start proxy. Check if cloud-sql-proxy is installed.[/red]")
                self.query_one("#start_proxy", Button).disabled = False

        except FileNotFoundError:
            log.write("[red]✗ Error: /usr/local/bin/cloud-sql-proxy not found[/red]")
            log.write("[yellow]Please install cloud-sql-proxy first[/yellow]")
            self.show_status("[red]cloud-sql-proxy not found. Please install it first.[/red]")
            self.query_one("#start_proxy", Button).disabled = False
        except Exception as e:
            log.write(f"[red]✗ Unexpected error: {str(e)}[/red]")
            self.show_status("[red]An unexpected error occurred.[/red]")
            self.query_one("#start_proxy", Button).disabled = False

    def show_status(self, message: str):
        """Display a status message."""
        status_widget = self.query_one("#status_message", Static)
        status_widget.update(f"\n{message}")


class Stage3Screen(Container):
    """Stage 3: Get database credentials."""

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]Stage 3: Database Credentials[/bold]\n")
        yield Static("Please provide your database credentials.\n")
        yield Label("Username:")
        yield Input(
            placeholder="Enter username (default: readonly)",
            value="readonly",
            id="username"
        )
        yield Label("Password:")
        yield Input(
            placeholder="Enter password",
            password=True,
            id="password"
        )
        yield Horizontal(
            Button("Continue", variant="primary", id="continue"),
            Button("Back", variant="default", id="back"),
            Button("Quit", variant="error", id="quit"),
        )
        yield Static(id="error_message")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "back":
            self.app_instance.move_to_stage_2()
        elif event.button.id == "continue":
            username_widget = self.query_one("#username", Input)
            password_widget = self.query_one("#password", Input)

            username = username_widget.value.strip() or "readonly"
            password = password_widget.value

            if not username:
                self.show_error("Please enter a username")
                return

            if not password:
                self.show_error("Please enter a password")
                return

            self.app_instance.db_username = username
            self.app_instance.db_password = password
            self.show_error(f"[green]✓ Credentials set for user: {username}[/green]")
            self.app_instance.move_to_stage_4()

    def show_error(self, message: str):
        """Display an error or success message."""
        error_widget = self.query_one("#error_message", Static)
        error_widget.update(f"\n{message}")


class Stage4Screen(Container):
    """Stage 4: Extract database schema."""

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.last_error_message = ""

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]Stage 4: Extract Database Schema[/bold]\n")
        yield Static("Configure database connection and output file for schema extraction.\n")

        yield Label("Database Host:")
        yield Input(value="127.0.0.1", id="db_host")

        yield Label("Database Port:")
        yield Input(value="2021", id="db_port")

        yield Label("Database Name:")
        yield Input(value="arXiv", id="db_name")

        yield Label("Output File:")
        yield Input(
            value="arxiv/db/arxiv_db_schema.sql",
            placeholder="Path to save schema",
            id="output_file"
        )

        yield Horizontal(
            Button("Extract Schema", variant="primary", id="extract"),
            Button("Next", variant="success", id="continue", disabled=True),
            Button("Back", variant="default", id="back"),
            Button("Quit", variant="error", id="quit"),
            id="main_buttons"
        )
        yield LoadingIndicator()
        yield Static(id="status_message")
        yield RichLog(id="output_log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.query_one(LoadingIndicator).display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "back":
            self.app_instance.move_to_stage_3()
        elif event.button.id == "extract":
            self.run_schema_extraction()
        elif event.button.id == "continue":
            self.app_instance.move_to_stage_5()
        elif event.button.id == "copy_error":
            self.copy_error_to_clipboard()

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def run_schema_extraction(self):
        """Execute mysqldump to extract schema."""
        host = self.query_one("#db_host", Input).value
        port = self.query_one("#db_port", Input).value
        db_name = self.query_one("#db_name", Input).value
        output_file = self.query_one("#output_file", Input).value

        username = self.app_instance.db_username
        password = self.app_instance.db_password

        if not all([host, port, db_name, output_file, username, password]):
            self.show_status("[red]Error: All fields are required[/red]")
            return

        # Disable navigation while extraction is running.
        self.query_one("#extract", Button).disabled = True
        self.query_one("#continue", Button).disabled = True
        self.show_status("[yellow]Running mysqldump...[/yellow]")
        self.query_one(LoadingIndicator).display = True

        mysqldump_cmd = [
            "mysqldump", "-h", host, "--port", port, "-u", username, f"-p{password}",
            "--no-data", "--set-gtid-purged=OFF", "--skip-comments", db_name
        ]
        sed_cmd = ["sed", "s/ AUTO_INCREMENT=[0-9]*\\b/ AUTO_INCREMENT=1/"]

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        log = self.query_one("#output_log", RichLog)
        log.clear()
        log.write(f"[cyan]Executing:[/cyan] mysqldump -h {host} --port {port} -u {username} -p*** ... | {' '.join(sed_cmd)}")
        log.write(f"[cyan]Output file:[/cyan] {output_file}")

        threading.Thread(
            target=self.extract_schema_worker,
            args=(mysqldump_cmd, sed_cmd, output_path, log),
            daemon=True,
        ).start()

    def on_extraction_success(self, output_path: Path):
        """Callback for successful schema extraction."""
        self.query_one(LoadingIndicator).display = False
        log = self.query_one("#output_log", RichLog)

        final_size = self.format_file_size(output_path.stat().st_size)
        log.write(f"[green]✓ Schema extracted successfully to {output_path}[/green]")
        log.write(f"[green]Final size: {final_size}[/green]")
        self.show_status("[green]✓ Schema extraction complete! Click Next to proceed, or re-run extraction.[/green]")

        self.app_instance.schema_file = output_path

        self.query_one("#extract", Button).disabled = False
        self.query_one("#continue", Button).disabled = False

    def on_extraction_failure(self, error_msg: str):
        """Callback for failed schema extraction."""
        self.query_one(LoadingIndicator).display = False
        log = self.query_one("#output_log", RichLog)

        log.write(f"[red]✗ Error: {error_msg}[/red]")
        self.last_error_message = f"mysqldump error:\n{error_msg}"
        self.show_status("[red]Schema extraction failed. Check the log above.[/red]")
        self.query_one("#extract", Button).disabled = False
        self.query_one("#continue", Button).disabled = True
        self.add_copy_error_button()

    def extract_schema_worker(self, mysqldump_cmd: list[str], sed_cmd: list[str], output_path: Path, log: RichLog):
        """Worker to extract database schema using mysqldump and sed."""
        temp_output = output_path.with_suffix('.tmp')

        try:
            p_mysqldump = subprocess.Popen(mysqldump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            p_sed = subprocess.Popen(sed_cmd, stdin=p_mysqldump.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            p_mysqldump.stdout.close()

            table_count = 0
            with temp_output.open('w') as f:
                for line in p_sed.stdout:
                    f.write(line)
                    if line.startswith("CREATE TABLE"):
                        table_count += 1
                        if table_count % 10 == 0:
                            size_str = self.format_file_size(f.tell())
                            self.app.call_from_thread(
                                log.write,
                                f"[yellow]Extracting... {table_count} tables found ({size_str})[/yellow]"
                            )

            p_sed.wait()
            p_mysqldump.wait()

            if p_mysqldump.returncode != 0 or p_sed.returncode != 0:
                error = p_mysqldump.stderr.read() + p_sed.stderr.read()
                raise RuntimeError(error)

            temp_output.replace(output_path)
            self.app.call_from_thread(self.on_extraction_success, output_path)

        except Exception as e:
            if temp_output.exists():
                temp_output.unlink()
            self.app.call_from_thread(self.on_extraction_failure, str(e))

    def add_copy_error_button(self):
        """Add a copy error button if it doesn't exist."""
        button_container = self.query_one("#main_buttons", Horizontal)
        if not self.query_one_or_none("#copy_error"):
            button_container.mount(Button("Copy Error", variant="warning", id="copy_error"))

    def copy_error_to_clipboard(self):
        """Copy the error message to clipboard."""
        if not self.last_error_message:
            return

        try:
            import pyperclip
            pyperclip.copy(self.last_error_message)
            self.show_status("[green]✓ Error message copied to clipboard![/green]")
        except ImportError:
            try:
                subprocess.run(["xclip", "-selection", "clipboard"], input=self.last_error_message, text=True, check=True)
                self.show_status("[green]✓ Error message copied to clipboard![/green]")
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    subprocess.run(["pbcopy"], input=self.last_error_message, text=True, check=True)
                    self.show_status("[green]✓ Error message copied to clipboard![/green]")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    self.show_status("[yellow]Install pyperclip, xclip, or pbcopy to copy to clipboard[/yellow]")

    def show_status(self, message: str):
        """Display a status message."""
        status_widget = self.query_one("#status_message", Static)
        status_widget.update(f"\n{message}")


class Stage5Screen(Container):
    """Stage 5: Run code generation."""

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.output_log_content = ""

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]Stage 5: Generate Code from Schema[/bold]\n")
        yield Static("Run the code generator to create models from the database schema.\n")

        yield Label("Code Generator Script:")
        yield Input(
            value="development/db_codegen.py",
            placeholder="Path to db_codegen.py",
            id="codegen_script"
        )

        yield Label("MySQL Port:")
        yield Input(
            value="33602",
            placeholder="MySQL port (default: 33602)",
            id="mysql_port"
        )

        yield Checkbox("Enable SSL/TLS", id="ssl_enabled", value=True)

        yield Horizontal(
            Button("Generate Code", variant="primary", id="generate"),
            Button("Back", variant="default", id="back"),
            Button("Quit", variant="error", id="quit"),
            id="main_buttons"
        )
        yield LoadingIndicator()
        yield Static(id="status_message")
        yield RichLog(id="output_log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.query_one(LoadingIndicator).display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "back":
            self.app_instance.move_to_stage_4()
        elif event.button.id == "generate":
            self.run_code_generation()
        elif event.button.id == "copy_output":
            self.copy_output_to_clipboard()

    def run_code_generation(self):
        """Execute the code generation script."""
        codegen_script = self.query_one("#codegen_script", Input).value
        mysql_port = self.query_one("#mysql_port", Input).value
        ssl_enabled = self.query_one("#ssl_enabled", Checkbox).value

        if not all([codegen_script, mysql_port]):
            self.show_status("[red]Error: All fields are required[/red]")
            return

        try:
            int(mysql_port)
        except ValueError:
            self.show_status(f"[red]Error: Invalid port number: {mysql_port}[/red]")
            return

        dev_dir_path = Path(os.path.abspath(__file__)).parent
        arxiv_base_dir_path = dev_dir_path.parent
        script_path = arxiv_base_dir_path / codegen_script
        if not script_path.exists():
            self.show_status(f"[red]Error: Script '{codegen_script}' does not exist[/red]")
            return

        self.query_one("#generate", Button).disabled = True
        self.show_status("[yellow]Running code generation...[/yellow]")
        self.query_one(LoadingIndicator).display = True

        log = self.query_one("#output_log", RichLog)
        log.clear()

        cmd = ["python", str(script_path), "--mysql-port", mysql_port]
        if not ssl_enabled:
            cmd.append("--no-ssl")

        log.write(f"[cyan]Executing:[/cyan] {' '.join(cmd)}")
        self.output_log_content = f"Command: {' '.join(cmd)}\n\n"

        threading.Thread(
            target=self.code_generation_worker,
            args=(cmd, arxiv_base_dir_path, log),
            daemon=True,
        ).start()

    def on_codegen_success(self, stdout: str, stderr: str):
        """Callback for successful code generation."""
        self.query_one(LoadingIndicator).display = False
        log = self.query_one("#output_log", RichLog)

        if stdout:
            self.output_log_content += "=== Output ===\n" + stdout + "\n"
        if stderr:
            log.write("[yellow]Warnings/Info:[/yellow]")
            log.write(stderr)
            self.output_log_content += "=== Warnings/Info ===\n" + stderr + "\n"

        success_msg = "✓ Code generation completed successfully"
        log.write(f"[green]{success_msg}[/green]")
        self.output_log_content += success_msg + "\n"

        log_file = Path("development/db_codegen_log.txt")
        log_file.write_text(self.output_log_content)
        log.write(f"[cyan]Log saved to: {log_file}[/cyan]")

        self.show_status(f"[green]✓ Code generation complete! Log saved to {log_file}[/green]")
        self.query_one("#generate", Button).disabled = False
        self.add_copy_output_button()

    def on_codegen_failure(self, returncode: int, stdout: str, stderr: str):
        """Callback for failed code generation."""
        self.query_one(LoadingIndicator).display = False
        log = self.query_one("#output_log", RichLog)

        error_msg = f"✗ Error (exit code {returncode})"
        log.write(f"[red]{error_msg}[/red]")
        self.output_log_content += f"{error_msg}\n\n"

        if stdout:
            self.output_log_content += "=== Output ===\n" + stdout + "\n"
        if stderr:
            log.write("[red]Error output:[/red]")
            log.write(stderr)
            self.output_log_content += "=== Error Output ===\n" + stderr + "\n"

        log_file = Path("development/db_codegen_log.txt")
        log_file.write_text(self.output_log_content)
        log.write(f"[cyan]Error log saved to: {log_file}[/cyan]")

        self.show_status(f"[red]Code generation failed. Log saved to {log_file}[/red]")
        self.query_one("#generate", Button).disabled = False
        self.add_copy_output_button()

    def code_generation_worker(self, cmd: list[str], cwd: Path, log: RichLog):
        """Worker to run the code generation script."""
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=cwd.as_posix()
            )

            stdout_lines = []
            with process.stdout:
                for line in iter(process.stdout.readline, ''):
                    self.app.call_from_thread(log.write, line.rstrip())
                    stdout_lines.append(line)

            stderr_output = process.stderr.read()
            return_code = process.wait()
            stdout_output = "".join(stdout_lines)

            if return_code != 0:
                self.app.call_from_thread(self.on_codegen_failure, return_code, stdout_output, stderr_output)
            else:
                self.app.call_from_thread(self.on_codegen_success, stdout_output, stderr_output)

        except Exception as e:
            self.app.call_from_thread(self.on_codegen_failure, -1, "", str(e))

    def add_copy_output_button(self):
        """Add a copy output button if it doesn't exist."""
        button_container = self.query_one("#main_buttons", Horizontal)
        if self.query_optional("#copy_output") is None:
            button_container.mount(Button("Copy Output", variant="warning", id="copy_output"))

    def query_optional(self, selector: str):
        """Return a widget matching selector, or None if it does not exist."""
        try:
            return self.query_one(selector)
        except Exception:
            return None

    def copy_output_to_clipboard(self):
        """Copy the output log to clipboard."""
        if not self.output_log_content:
            self.show_status("[yellow]No output to copy[/yellow]")
            return

        try:
            import pyperclip
            pyperclip.copy(self.output_log_content)
            self.show_status("[green]✓ Output copied to clipboard![/green]")
        except ImportError:
            try:
                subprocess.run(["xclip", "-selection", "clipboard"], input=self.output_log_content, text=True, check=True)
                self.show_status("[green]✓ Output copied to clipboard![/green]")
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    subprocess.run(["pbcopy"], input=self.output_log_content, text=True, check=True)
                    self.show_status("[green]✓ Output copied to clipboard![/green]")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    self.show_status("[yellow]Install pyperclip, xclip, or pbcopy to copy to clipboard[/yellow]")

    def show_status(self, message: str):
        """Display a status message."""
        status_widget = self.query_one("#status_message", Static)
        status_widget.update(f"\n{message}")


class DatabaseCodegenApp(App):
    """Interactive TUI application for database code generation."""

    CSS = """
    Screen {
        align: center middle;
    }

    StageIndicator {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        padding: 1;
    }

    Container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    Input {
        margin: 1 0;
    }

    Horizontal {
        height: auto;
        margin-top: 2;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }

    #error_message, #status_message {
        margin-top: 1;
        color: $error;
    }

    #output_log {
        margin-top: 1;
        height: 10;
        border: solid $primary;
        background: $surface;
    }

    LoadingIndicator {
        display: none;
        margin-top: 1;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    TITLE = "Database Code Generator"

    def __init__(self):
        super().__init__()
        self.replica_name: Optional[str] = None
        self.proxy_port: Optional[str] = None
        self.proxy_process: Optional[subprocess.Popen] = None
        self.db_username: Optional[str] = None
        self.db_password: Optional[str] = None
        self.schema_file: Optional[Path] = None
        self.stage_indicator = StageIndicator(total_stages=5)
        self.current_stage = 1

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield self.stage_indicator
        yield Stage1Screen(self)
        yield Footer()

    def action_quit(self):
        """Handle quit action."""
        self.cleanup_proxy()
        self.exit()

    def cleanup_proxy(self):
        """Stop the proxy process if running."""
        if self.proxy_process and self.proxy_process.poll() is None:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proxy_process.kill()
            except Exception:
                pass

    def on_unmount(self):
        """Cleanup when app is unmounted."""
        self.cleanup_proxy()

    def move_to_stage_1(self):
        """Navigate to Stage 1."""
        self.current_stage = 1
        self.stage_indicator.set_stage(1)
        container = self.query_one(Container)
        container.remove()
        self.mount(Stage1Screen(self))

    def move_to_stage_2(self):
        """Navigate to Stage 2."""
        self.current_stage = 2
        self.stage_indicator.set_stage(2)
        container = self.query_one(Container)
        container.remove()
        self.mount(Stage2Screen(self))

    def move_to_stage_3(self):
        """Navigate to Stage 3."""
        self.current_stage = 3
        self.stage_indicator.set_stage(3)
        container = self.query_one(Container)
        container.remove()
        self.mount(Stage3Screen(self))

    def move_to_stage_4(self):
        """Navigate to Stage 4."""
        self.current_stage = 4
        self.stage_indicator.set_stage(4)
        container = self.query_one(Container)
        container.remove()
        self.mount(Stage4Screen(self))

    def move_to_stage_5(self):
        """Navigate to Stage 5."""
        self.current_stage = 5
        self.stage_indicator.set_stage(5)
        container = self.query_one(Container)
        container.remove()
        self.mount(Stage5Screen(self))


def main():
    """Main entry point for the application."""
    app = DatabaseCodegenApp()
    app.run()


if __name__ == "__main__":
    main()