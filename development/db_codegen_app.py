#!/usr/bin/env python
"""
Interactive Database Code Generator Application

A multi-stage TUI application for generating code from database schemas.
"""

import sys
import subprocess
import socket
import time
import threading
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Label, RichLog, Checkbox
from textual.binding import Binding
from textual.validation import ValidationResult, Validator
from textual.worker import Worker, WorkerState


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

        # Check if schema file exists to show skip button
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
            # Store the schema file path
            self.app_instance.schema_file = Path("arxiv/db/arxiv_db_schema.sql")
            self.app_instance.move_to_stage_5()
        elif event.button.id == "continue":
            replica_widget = self.query_one("#replica_name", Input)
            replica_name = replica_widget.value.strip() or "arxiv-production-rep11"

            if not replica_name:
                self.show_error("Please enter a replica name")
                return

            # Store the replica name
            self.app_instance.replica_name = replica_name
            self.show_error(f"[green]✓ Replica name set: {replica_name}[/green]")

            # Move to next stage
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

        # Disable start button during execution
        self.query_one("#start_proxy", Button).disabled = True
        self.show_status("[yellow]Checking proxy status...[/yellow]")

        log = self.query_one("#output_log", RichLog)
        log.clear()

        # Check if port is already in use
        try:
            port_num = int(proxy_port)
        except ValueError:
            log.write(f"[red]✗ Invalid port number: {proxy_port}[/red]")
            self.show_status("[red]Invalid port number[/red]")
            self.query_one("#start_proxy", Button).disabled = False
            return

        if self.is_port_in_use(port_num):
            log.write(f"[yellow]Port {proxy_port} is already in use[/yellow]")
            log.write(f"[green]✓ Assuming Cloud SQL Proxy is already running[/green]")
            log.write(f"[green]Proxy appears to be running on 0.0.0.0:{proxy_port}[/green]")
            self.show_status(f"[green]✓ Proxy already running! Click Continue to proceed.[/green]")

            # Store the proxy port
            self.app_instance.proxy_port = proxy_port

            # Replace Start button with Continue button
            button_container = self.query_one(Horizontal)
            start_btn = self.query_one("#start_proxy", Button)
            start_btn.remove()
            button_container.mount(Button("Continue", variant="success", id="continue"), before=0)
            return

        # Build the cloud-sql-proxy command
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
            # Start the proxy in the background
            self.app_instance.proxy_process = subprocess.Popen(
                proxy_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Store the proxy port
            self.app_instance.proxy_port = proxy_port

            # Give it a moment to start
            import time
            time.sleep(2)

            # Check if process is still running
            if self.app_instance.proxy_process.poll() is None:
                log.write(f"[green]✓ Cloud SQL Proxy started successfully (PID: {self.app_instance.proxy_process.pid})[/green]")
                log.write(f"[green]Proxy is running on 0.0.0.0:{proxy_port}[/green]")
                self.show_status(f"[green]✓ Proxy running! Click Continue to proceed.[/green]")

                # Replace Start button with Continue button
                button_container = self.query_one(Horizontal)
                start_btn = self.query_one("#start_proxy", Button)
                start_btn.remove()
                button_container.mount(Button("Continue", variant="success", id="continue"), before=0)
            else:
                log.write(f"[red]✗ Proxy process terminated unexpectedly[/red]")
                self.show_status("[red]Failed to start proxy. Check if cloud-sql-proxy is installed.[/red]")
                self.query_one("#start_proxy", Button).disabled = False

        except FileNotFoundError:
            log.write(f"[red]✗ Error: /usr/local/bin/cloud-sql-proxy not found[/red]")
            log.write(f"[yellow]Please install cloud-sql-proxy first[/yellow]")
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

            # Store the credentials
            self.app_instance.db_username = username
            self.app_instance.db_password = password
            self.show_error(f"[green]✓ Credentials set for user: {username}[/green]")

            # Move to next stage
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
        self.monitor_thread = None
        self.monitoring_active = False

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
            Button("Back", variant="default", id="back"),
            Button("Quit", variant="error", id="quit"),
            id="main_buttons"
        )
        yield Static(id="status_message")
        yield RichLog(id="output_log", wrap=True, highlight=True, markup=True)

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
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def monitor_file_progress(self, output_path: Path, log: RichLog):
        """Monitor file size in a separate thread."""
        last_size = 0
        while self.monitoring_active:
            try:
                if output_path.exists():
                    current_size = output_path.stat().st_size
                    if current_size != last_size:
                        size_str = self.format_file_size(current_size)
                        self.app.call_from_thread(
                            log.write,
                            f"[yellow]Writing... {size_str}[/yellow]"
                        )
                        last_size = current_size
            except Exception:
                pass
            time.sleep(1)  # Check every second

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

        # Disable extract button during execution
        self.query_one("#extract", Button).disabled = True
        self.show_status("[yellow]Running mysqldump...[/yellow]")

        # Build the mysqldump command
        mysqldump_cmd = [
            "mysqldump",
            "-h", host,
            "--port", port,
            "-u", username,
            f"-p{password}",
            "--no-data",
            "--set-gtid-purged=OFF",
            "--skip-comments",
            db_name
        ]

        # Build the sed command to normalize AUTO_INCREMENT
        sed_cmd = ["sed", "s/ AUTO_INCREMENT=[0-9]*\\b/ AUTO_INCREMENT=1/"]

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        log = self.query_one("#output_log", RichLog)
        log.clear()
        log.write(f"[cyan]Executing:[/cyan] mysqldump -h {host} --port {port} -u {username} -p*** --no-data --set-gtid-purged=OFF --skip-comments {db_name}")
        log.write(f"[cyan]Output file:[/cyan] {output_file}")

        # Create a temporary file for monitoring
        temp_output = output_path.with_suffix('.tmp')

        # Start file monitoring in background thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self.monitor_file_progress,
            args=(temp_output, log),
            daemon=True
        )
        self.monitor_thread.start()

        try:
            # Run mysqldump and write to temp file immediately
            log.write(f"[yellow]Starting extraction...[/yellow]")

            with open(temp_output, 'w') as temp_f:
                # Run mysqldump
                result1 = subprocess.run(
                    mysqldump_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Run sed to normalize AUTO_INCREMENT
                result2 = subprocess.run(
                    sed_cmd,
                    input=result1.stdout,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Write to temp file
                temp_f.write(result2.stdout)

            # Stop monitoring
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)

            # Move temp file to final location
            temp_output.replace(output_path)

            final_size = self.format_file_size(output_path.stat().st_size)
            log.write(f"[green]✓ Schema extracted successfully to {output_file}[/green]")
            log.write(f"[green]Final size: {final_size}[/green]")
            self.show_status(f"[green]✓ Schema extraction complete! Click Continue to proceed.[/green]")

            # Store the output file path
            self.app_instance.schema_file = output_path

            # Replace Extract button with Continue button
            button_container = self.query_one("#main_buttons", Horizontal)
            extract_btn = self.query_one("#extract", Button)
            extract_btn.remove()
            button_container.mount(Button("Continue", variant="success", id="continue"), before=0)

        except subprocess.CalledProcessError as e:
            # Stop monitoring
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)

            # Clean up temp file
            if temp_output.exists():
                temp_output.unlink()

            error_msg = e.stderr if e.stderr else str(e)
            log.write(f"[red]✗ Error: {error_msg}[/red]")

            # Store error message for copying
            self.last_error_message = f"mysqldump error:\n{error_msg}"

            self.show_status("[red]Schema extraction failed. Check the log above.[/red]")
            self.query_one("#extract", Button).disabled = False

            # Add copy error button
            self.add_copy_error_button()

        except Exception as e:
            # Stop monitoring
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)

            # Clean up temp file
            if temp_output.exists():
                temp_output.unlink()

            error_msg = str(e)
            log.write(f"[red]✗ Unexpected error: {error_msg}[/red]")

            # Store error message for copying
            self.last_error_message = f"Unexpected error:\n{error_msg}"

            self.show_status("[red]An unexpected error occurred.[/red]")
            self.query_one("#extract", Button).disabled = False

            # Add copy error button
            self.add_copy_error_button()

    def add_copy_error_button(self):
        """Add a copy error button if it doesn't exist."""
        button_container = self.query_one("#main_buttons", Horizontal)
        # Check if copy button already exists
        try:
            self.query_one("#copy_error", Button)
        except:
            # Button doesn't exist, add it
            button_container.mount(Button("Copy Error", variant="warning", id="copy_error"))

    def copy_error_to_clipboard(self):
        """Copy the error message to clipboard."""
        if not self.last_error_message:
            return

        try:
            # Try using pyperclip if available
            import pyperclip
            pyperclip.copy(self.last_error_message)
            self.show_status("[green]✓ Error message copied to clipboard![/green]")
        except ImportError:
            # Fall back to xclip/pbcopy
            try:
                # Try xclip (Linux)
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=self.last_error_message,
                    text=True,
                    check=True
                )
                self.show_status("[green]✓ Error message copied to clipboard![/green]")
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    # Try pbcopy (macOS)
                    subprocess.run(
                        ["pbcopy"],
                        input=self.last_error_message,
                        text=True,
                        check=True
                    )
                    self.show_status("[green]✓ Error message copied to clipboard![/green]")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # If all else fails, just show the message
                    self.show_status("[yellow]Install pyperclip, xclip, or use pbcopy to copy to clipboard[/yellow]")

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
            value="13306",
            placeholder="MySQL port (default: 13306)",
            id="mysql_port"
        )

        yield Checkbox("Enable SSL/TLS", id="ssl_enabled", value=True)

        yield Horizontal(
            Button("Generate Code", variant="primary", id="generate"),
            Button("Back", variant="default", id="back"),
            Button("Quit", variant="error", id="quit"),
            id="main_buttons"
        )
        yield Static(id="status_message")
        yield RichLog(id="output_log", wrap=True, highlight=True, markup=True)

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

        if not codegen_script:
            self.show_status("[red]Error: Code generator script path is required[/red]")
            return

        if not mysql_port:
            self.show_status("[red]Error: MySQL port is required[/red]")
            return

        # Validate port is a number
        try:
            port_num = int(mysql_port)
        except ValueError:
            self.show_status(f"[red]Error: Invalid port number: {mysql_port}[/red]")
            return

        script_path = Path(codegen_script)
        if not script_path.exists():
            self.show_status(f"[red]Error: Script '{codegen_script}' does not exist[/red]")
            return

        # Disable generate button during execution
        self.query_one("#generate", Button).disabled = True
        self.show_status("[yellow]Running code generation...[/yellow]")

        log = self.query_one("#output_log", RichLog)
        log.clear()

        # Build command with optional --no-ssl flag
        cmd = ["python", str(script_path), "--mysql-port", mysql_port]
        if not ssl_enabled:
            cmd.append("--no-ssl")

        cmd_str = ' '.join(cmd)
        log.write(f"[cyan]Executing:[/cyan] {cmd_str}")

        # Initialize log content with command
        self.output_log_content = f"Command: {cmd_str}\n\n"

        try:
            # Run the code generation script with arguments
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=Path.cwd()
            )

            # Display and save stdout
            if result.stdout:
                log.write("[green]Output:[/green]")
                self.output_log_content += "=== Output ===\n"
                for line in result.stdout.splitlines():
                    log.write(line)
                    self.output_log_content += line + "\n"
                self.output_log_content += "\n"

            # Display and save stderr if any (warnings, etc.)
            if result.stderr:
                log.write("[yellow]Warnings/Info:[/yellow]")
                self.output_log_content += "=== Warnings/Info ===\n"
                for line in result.stderr.splitlines():
                    log.write(line)
                    self.output_log_content += line + "\n"
                self.output_log_content += "\n"

            success_msg = "✓ Code generation completed successfully"
            log.write(f"[green]{success_msg}[/green]")
            self.output_log_content += success_msg + "\n"

            # Save log to file
            log_file = Path("development/db_codegen_log.txt")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(self.output_log_content)

            log.write(f"[cyan]Log saved to: {log_file}[/cyan]")
            self.show_status(f"[green]✓ Code generation complete! Log saved to {log_file}[/green]")

            # Enable button and add copy button
            self.query_one("#generate", Button).disabled = False
            self.add_copy_output_button()

        except subprocess.CalledProcessError as e:
            error_msg = f"✗ Error (exit code {e.returncode})"
            log.write(f"[red]{error_msg}[/red]")
            self.output_log_content += f"{error_msg}\n\n"

            if e.stdout:
                log.write("[yellow]Output:[/yellow]")
                self.output_log_content += "=== Output ===\n"
                for line in e.stdout.splitlines():
                    log.write(line)
                    self.output_log_content += line + "\n"
                self.output_log_content += "\n"

            if e.stderr:
                log.write("[red]Error output:[/red]")
                self.output_log_content += "=== Error Output ===\n"
                for line in e.stderr.splitlines():
                    log.write(line)
                    self.output_log_content += line + "\n"
                self.output_log_content += "\n"

            # Save error log to file
            log_file = Path("development/db_codegen_log.txt")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(self.output_log_content)

            log.write(f"[cyan]Error log saved to: {log_file}[/cyan]")
            self.show_status(f"[red]Code generation failed. Log saved to {log_file}[/red]")
            self.query_one("#generate", Button).disabled = False
            self.add_copy_output_button()

        except Exception as e:
            error_msg = f"✗ Unexpected error: {str(e)}"
            log.write(f"[red]{error_msg}[/red]")
            self.output_log_content += f"{error_msg}\n"

            # Save error log to file
            log_file = Path("development/db_codegen_log.txt")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(self.output_log_content)

            log.write(f"[cyan]Error log saved to: {log_file}[/cyan]")
            self.show_status(f"[red]An unexpected error occurred. Log saved to {log_file}[/red]")
            self.query_one("#generate", Button).disabled = False
            self.add_copy_output_button()

    def add_copy_output_button(self):
        """Add a copy output button if it doesn't exist."""
        button_container = self.query_one("#main_buttons", Horizontal)
        # Check if copy button already exists
        try:
            self.query_one("#copy_output", Button)
        except:
            # Button doesn't exist, add it
            button_container.mount(Button("Copy Output", variant="warning", id="copy_output"))

    def copy_output_to_clipboard(self):
        """Copy the output log to clipboard."""
        if not self.output_log_content:
            self.show_status("[yellow]No output to copy[/yellow]")
            return

        try:
            # Try using pyperclip if available
            import pyperclip
            pyperclip.copy(self.output_log_content)
            self.show_status("[green]✓ Output copied to clipboard![/green]")
        except ImportError:
            # Fall back to xclip/pbcopy
            try:
                # Try xclip (Linux)
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=self.output_log_content,
                    text=True,
                    check=True
                )
                self.show_status("[green]✓ Output copied to clipboard![/green]")
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    # Try pbcopy (macOS)
                    subprocess.run(
                        ["pbcopy"],
                        input=self.output_log_content,
                        text=True,
                        check=True
                    )
                    self.show_status("[green]✓ Output copied to clipboard![/green]")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # If all else fails, just show the message
                    self.show_status("[yellow]Install pyperclip, xclip, or use pbcopy to copy to clipboard[/yellow]")

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
                pass  # Best effort cleanup

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
