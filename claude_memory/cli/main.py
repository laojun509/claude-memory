"""CLI interface for Claude Memory."""
import typer
from rich import print
from rich.table import Table
from pathlib import Path

from claude_memory.core.engine import MemoryEngine

app = typer.Typer(help="Claude Memory - Intelligent memory for Claude Code")


@app.command()
def search(
    query: str,
    project: str = typer.Option("default", "--project", "-p"),
    limit: int = typer.Option(5, "--limit", "-n"),
):
    """Search memories"""
    engine = MemoryEngine()
    results = engine.search_memories(query, project_id=project, limit=limit)
    
    if not results:
        print("[yellow]No memories found.[/yellow]")
        return
    
    table = Table(title=f"Memories matching '{query}'")
    table.add_column("Type", style="cyan")
    table.add_column("Content", style="white")
    table.add_column("Importance", style="green")
    
    for mem in results:
        importance_str = "█" * int(mem.importance * 10) + "░" * (10 - int(mem.importance * 10))
        table.add_row(mem.entity_type.value, mem.content[:50], importance_str)
    
    print(table)


@app.command()
def list_memories(
    project: str = typer.Option("default", "--project", "-p"),
):
    """List all memories for a project"""
    engine = MemoryEngine()
    memories = engine.get_project_memories(project)
    
    if not memories:
        print(f"[yellow]No memories for project '{project}'.[/yellow]")
        return
    
    print(f"\n[bold]Project: {project}[/bold] ({len(memories)} memories)\n")
    
    for mem in memories:
        icon = {
            "preference": "💭",
            "fact": "📌",
            "project": "📁",
            "code_style": "💻",
            "decision": "✅",
            "task": "📋",
        }.get(mem.entity_type.value, "•")
        
        print(f"{icon} [{mem.entity_type.value}] {mem.content}")
        print(f"   Importance: {mem.importance:.1f} | ID: {mem.id}")
        print()


@app.command()
def stats():
    """Show memory statistics"""
    engine = MemoryEngine()
    print("[green]Memory system is running.[/green]")


if __name__ == "__main__":
    app()
