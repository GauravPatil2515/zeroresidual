import click
from rich.console import Console

console = Console(stderr=True)

@click.group()
def app():
    """ZeroResidual: The Open-Source UPI Settlement & Discrepancy Engine"""
    pass

@app.command()
@click.option("--version", is_flag=True, help="Show version")
def info(version):
    """Display ZeroResidual engine status and metadata."""
    console.print("[bold cyan]ZeroResidual v0.1.0[/bold cyan] · UPI Settlement & Discrepancy Engine")

if __name__ == "__main__":
    app()
