# /// script
# dependencies = ["fire", "rich"]
# ///
"""Command line interface for pystubnik using Fire."""

from pathlib import Path
from typing import Any

import fire
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from twat_coding.pystubnik.config import StubConfig
from twat_coding.pystubnik.processors.stub_generation import StubGenerator


class PystubnikCLI:
    """CLI interface for pystubnik."""

    def __init__(self) -> None:
        """Initialize the CLI interface."""
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
        )

    def generate(
        self,
        input_path: str,
        output_path: str | None = None,
        config_file: str | None = None,
        **config_kwargs: Any,
    ) -> None:
        """Generate stubs for a Python file.

        Args:
            input_path: Path to the Python file to generate stubs for
            output_path: Optional path to write the stub file to
            config_file: Optional path to a configuration file
            **config_kwargs: Additional configuration options

        """
        input_file = Path(input_path)
        if not input_file.exists():
            self.console.print(
                f"[red]Error: Input file {input_path} does not exist[/red]"
            )
            return

        # Load config from file if provided
        config_dict: dict[str, Any] = {}
        if config_file:
            config_path = Path(config_file)
            if not config_path.exists():
                self.console.print(
                    f"[red]Error: Config file {config_file} does not exist[/red]"
                )
                return
            # TODO: Load config from file

        # Update config with kwargs
        config_dict.update(config_kwargs)

        # Create output path if not provided
        if output_path is None:
            output_path = str(input_file.with_suffix(".pyi"))

        # Create config and generator
        config = StubConfig(
            input_path=input_file.parent,
            output_path=Path(output_path).parent,
            **config_dict,
        )
        generator = StubGenerator(config)

        # Generate stub
        with self.progress:
            task = self.progress.add_task(
                f"Generating stub for {input_path}...", total=None
            )
            try:
                stub_content = generator.generate_stub(input_file)
                Path(output_path).write_text(stub_content)
                self.progress.remove_task(task)
                self.console.print(
                    f"[green]Successfully generated stub at {output_path}[/green]"
                )
            except Exception as e:
                self.progress.remove_task(task)
                self.console.print(f"[red]Error generating stub: {e}[/red]")

    def generate_dir(
        self,
        input_dir: str,
        output_dir: str | None = None,
        config_file: str | None = None,
        **config_kwargs: Any,
    ) -> None:
        """Generate stubs for all Python files in a directory.

        Args:
            input_dir: Path to the directory containing Python files
            output_dir: Optional path to write the stub files to
            config_file: Optional path to a configuration file
            **config_kwargs: Additional configuration options

        """
        input_path = Path(input_dir)
        if not input_path.exists():
            self.console.print(
                f"[red]Error: Input directory {input_dir} does not exist[/red]"
            )
            return

        # Create output directory if not provided
        if output_dir is None:
            output_dir = str(input_path / "stubs")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Load config from file if provided
        config_dict: dict[str, Any] = {}
        if config_file:
            config_path = Path(config_file)
            if not config_path.exists():
                self.console.print(
                    f"[red]Error: Config file {config_file} does not exist[/red]"
                )
                return
            # TODO: Load config from file

        # Update config with kwargs
        config_dict.update(config_kwargs)

        # Create config and generator
        config = StubConfig(
            input_path=input_path,
            output_path=output_path,
            **config_dict,
        )
        generator = StubGenerator(config)

        # Find all Python files
        python_files = list(input_path.rglob("*.py"))
        if not python_files:
            self.console.print("[yellow]No Python files found in directory[/yellow]")
            return

        # Generate stubs
        with self.progress:
            task = self.progress.add_task(
                f"Generating stubs for {len(python_files)} files...",
                total=len(python_files),
            )
            for py_file in python_files:
                try:
                    rel_path = py_file.relative_to(input_path)
                    out_file = output_path / rel_path.with_suffix(".pyi")
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    stub_content = generator.generate_stub(py_file)
                    out_file.write_text(stub_content)
                    self.progress.advance(task)
                except Exception as e:
                    self.console.print(f"[red]Error processing {py_file}: {e}[/red]")

            self.progress.remove_task(task)
            self.console.print(
                f"[green]Successfully generated stubs in {output_dir}[/green]"
            )


def main() -> None:
    """Main entry point for the CLI."""
    fire.Fire(PystubnikCLI)
