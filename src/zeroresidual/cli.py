import sys
import os
import json
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zeroresidual.engine.recon import ReconciliationEngine
from zeroresidual.llm.gemma import GemmaClient

console = Console(stderr=True)  # Rich formatting to stderr so stdout remains pipeable JSON
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def execute_reconciliation(pos_csv: str, webhooks_json: str, bank_csv: str, no_llm: bool, model: str, as_json: bool):
    """Core executor for reconciliation runs."""
    gemma_client = GemmaClient(model_name=model) if not no_llm else None
    engine = ReconciliationEngine(gemma_client=gemma_client)

    is_llm_active = (not no_llm) and (gemma_client.is_available() if gemma_client else False)

    result = engine.reconcile(
        pos_csv_path=pos_csv,
        webhooks_json_path=webhooks_json,
        bank_csv_path=bank_csv,
        use_llm=is_llm_active
    )

    if as_json:
        # Output clean JSON to stdout for piping / CI
        print(json.dumps(result.model_dump(), default=str, indent=2))
        sys.exit(result.exit_code)

    # Render Terminal Presentation to stderr
    mode_tag = "[bold green]LLM: Google Gemma 2 (2B)[/bold green]" if is_llm_active else "[bold yellow]100% Deterministic Regex (--no-llm)[/bold yellow]"
    console.print(Panel.fit(
        f"[bold white]🏛️ ZERORESIDUAL[/bold white] · Open-Source UPI Settlement & Discrepancy Engine\n"
        f"Mode: {mode_tag} · Precision: [cyan]Decimal (Paise)[/cyan]",
        border_style="cyan"
    ))

    # Waterfall Table
    table = Table(title="📊 Settlement Waterfall Breakdown", border_style="dim", header_style="bold cyan")
    table.add_column("Step / Category", style="bold")
    table.add_column("Type", justify="center")
    table.add_column("Amount (₹)", justify="right")
    table.add_column("Count", justify="center")
    table.add_column("Audit Notes", style="dim")

    for step in result.waterfall:
        amt_str = f"₹{step.amount:,.2f}"
        if step.direction == "BASE":
            style = "bold white"
            dir_str = "BASE"
        elif step.direction == "SUBTRACT":
            style = "bold red"
            dir_str = "(-) DEDUCT"
            amt_str = f"- ₹{step.amount:,.2f}"
        elif step.direction == "RESULT":
            style = "bold cyan"
            dir_str = "(=) RESULT"
        else: # RESIDUAL
            if result.is_reconciled:
                style = "bold green"
                dir_str = "[OK] RESIDUAL"
            else:
                style = "bold yellow on red"
                dir_str = "[!] RESIDUAL"

        table.add_row(
            Text(step.label, style=style),
            dir_str,
            amt_str,
            str(step.count),
            step.notes
        )

    console.print(table)

    # Summary Panel
    if result.is_reconciled:
        summary_panel = Panel(
            f"[bold green]✓ RECONCILIATION COMPLETE: 100% TIED OUT[/bold green]\n"
            f"Gross Sales:        ₹{result.gross_pos_sales:,.2f}\n"
            f"Total Deductions:  - ₹{result.total_deductions:,.2f}\n"
            f"Bank Payout:        ₹{result.bank_received_payout:,.2f}\n"
            f"Residual:           [bold green]₹{result.residual:,.2f}[/bold green] (Zero math drift)\n\n"
            f"[bold]Merchant Explanation:[/bold]\n{result.explanation_en}",
            title="🎯 Verification Summary",
            border_style="green"
        )
    else:
        summary_panel = Panel(
            f"[bold red]🚨 UNEXPLAINED RESIDUAL DETECTED[/bold red]\n"
            f"Gross Sales:        ₹{result.gross_pos_sales:,.2f}\n"
            f"Total Deductions:  - ₹{result.total_deductions:,.2f}\n"
            f"Bank Payout:        ₹{result.bank_received_payout:,.2f}\n"
            f"Residual Shortfall: [bold red]₹{abs(result.residual):,.2f}[/bold red]\n\n"
            f"[bold yellow]Safety Guarantee:[/bold yellow] ZeroResidual refuses to guess or hallucinate explanations for missing funds. Flagged for bank escalation.\n"
            f"CI Process: Exiting with [bold red]code 1[/bold red].",
            title="⚠️ Audit Failure Alert",
            border_style="red"
        )
    console.print(summary_panel)

    sys.exit(result.exit_code)

@click.group()
def app():
    """ZeroResidual: Open-Source Settlement & Discrepancy Engine with Embedded Local Gemma 2 2B"""
    pass

@app.command()
@click.argument("pos_csv", type=click.Path(exists=True))
@click.argument("webhooks_json", type=click.Path(exists=True))
@click.argument("bank_csv", type=click.Path(exists=True))
@click.option("--no-llm", is_flag=True, default=False, help="Run strictly with deterministic regex rules without LLM")
@click.option("--model", default="gemma2:2b", help="Local Gemma model tag in Ollama")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output pure JSON to stdout for pipeline piping")
def run(pos_csv, webhooks_json, bank_csv, no_llm, model, as_json):
    """Reconcile 3 financial streams with Decimal precision and exit codes."""
    execute_reconciliation(pos_csv, webhooks_json, bank_csv, no_llm, model, as_json)

@app.command(name="demo-tieout")
@click.option("--no-llm", is_flag=True, default=False, help="Run strictly with deterministic regex rules without LLM")
@click.option("--model", default="gemma2:2b", help="Local Gemma model tag in Ollama")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output pure JSON to stdout")
def demo_tieout(no_llm, model, as_json):
    """Run live demo of Scenario 1 (Perfect Tie-Out: ₹50,000 to ₹43,000)."""
    p1 = os.path.join(DATA_DIR, "scenario_1_tieout", "pos_orders.csv")
    p2 = os.path.join(DATA_DIR, "scenario_1_tieout", "webhooks.json")
    p3 = os.path.join(DATA_DIR, "scenario_1_tieout", "bank_settlement.csv")
    execute_reconciliation(p1, p2, p3, no_llm, model, as_json)

@app.command(name="demo-unexplained")
@click.option("--no-llm", is_flag=True, default=False, help="Run strictly with deterministic regex rules without LLM")
@click.option("--model", default="gemma2:2b", help="Local Gemma model tag in Ollama")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output pure JSON to stdout")
def demo_unexplained(no_llm, model, as_json):
    """Run live demo of Scenario 2 (The Honest Residual: ₹212 Unexplained)."""
    p1 = os.path.join(DATA_DIR, "scenario_2_unexplained", "pos_orders.csv")
    p2 = os.path.join(DATA_DIR, "scenario_2_unexplained", "webhooks.json")
    p3 = os.path.join(DATA_DIR, "scenario_2_unexplained", "bank_settlement.csv")
    execute_reconciliation(p1, p2, p3, no_llm, model, as_json)

if __name__ == "__main__":
    app()
