"""Command-line interface for the real estate deal platform."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.agents.pipeline import PipelineAgent
from src.agents.market_research import MarketResearchAgent
from src.agents.deal_analyzer import DealAnalyzerAgent
from src.analysis.sensitivity import SensitivityAnalyzer
from src.models.deal import InvestmentStrategy
from src.models.financials import LoanTerms
from src.scrapers.mock_scraper import MockScraper
from src.utils.formatting import format_currency, format_percent, format_score

app = typer.Typer(
    name="deals",
    help="Real Estate Deal Sourcing & Analysis Platform",
    add_completion=False,
)
console = Console()


@app.command()
def search(
    markets: Optional[str] = typer.Option(
        None,
        "--markets", "-m",
        help="Comma-separated market IDs (e.g., 'indianapolis_in,cleveland_oh')",
    ),
    strategy: str = typer.Option(
        "cash_flow",
        "--strategy", "-s",
        help="Investment strategy: cash_flow, appreciation, value_add",
    ),
    max_price: Optional[float] = typer.Option(
        None,
        "--max-price", "-p",
        help="Maximum property price",
    ),
    min_beds: int = typer.Option(
        2,
        "--min-beds", "-b",
        help="Minimum bedrooms",
    ),
    down_payment: float = typer.Option(
        0.25,
        "--down-payment", "-d",
        help="Down payment percentage (0.0-1.0)",
    ),
    interest_rate: float = typer.Option(
        0.07,
        "--rate", "-r",
        help="Interest rate (0.0-1.0)",
    ),
    top_n: int = typer.Option(
        10,
        "--top", "-n",
        help="Number of top deals to show",
    ),
    sensitivity: bool = typer.Option(
        False,
        "--sensitivity/--no-sensitivity",
        help="Run stress tests",
    ),
):
    """Search for investment properties and rank by potential."""
    console.print(Panel.fit(
        "[bold blue]Real Estate Deal Finder[/bold blue]\n"
        "Searching for investment opportunities...",
        border_style="blue",
    ))

    # Parse markets
    market_ids = None
    if markets:
        market_ids = [m.strip() for m in markets.split(",")]

    # Parse strategy
    try:
        inv_strategy = InvestmentStrategy(strategy)
    except ValueError:
        console.print(f"[red]Invalid strategy: {strategy}[/red]")
        raise typer.Exit(1)

    # Create loan terms
    loan_terms = LoanTerms(
        down_payment_pct=down_payment,
        interest_rate=interest_rate,
    )

    # Run pipeline
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running deal pipeline...", total=None)

        pipeline = PipelineAgent()
        result = asyncio.run(pipeline.run(
            market_ids=market_ids,
            strategy=inv_strategy,
            max_price=max_price,
            min_beds=min_beds,
            top_n=top_n,
            loan_terms=loan_terms,
            run_sensitivity=sensitivity,
        ))

        progress.update(task, completed=True)

    if not result.success and not result.data.get("deals"):
        console.print("[red]No deals found matching criteria[/red]")
        if result.errors:
            for error in result.errors:
                console.print(f"[yellow]  {error}[/yellow]")
        raise typer.Exit(1)

    # Display results
    deals = result.data["deals"]
    _display_deals_table(deals)

    # Summary
    console.print(f"\n[dim]Analyzed {result.data['properties_scraped']} properties "
                  f"from {result.data['markets_analyzed']} markets[/dim]")
    console.print(f"[dim]Pipeline completed in {result.duration_ms}ms[/dim]")


@app.command()
def markets(
    top_n: int = typer.Option(
        10,
        "--top", "-n",
        help="Number of markets to show",
    ),
    strategy: str = typer.Option(
        "overall",
        "--strategy", "-s",
        help="Sort by: overall, cash_flow, growth",
    ),
):
    """List and rank investment markets."""
    console.print("[bold]Analyzing markets...[/bold]\n")

    agent = MarketResearchAgent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Researching markets...", total=None)
        result = asyncio.run(agent.run())
        progress.update(task, completed=True)

    if not result.success:
        console.print("[red]Failed to analyze markets[/red]")
        raise typer.Exit(1)

    markets = result.data["markets"]

    # Sort by strategy
    if strategy == "cash_flow":
        markets.sort(key=lambda x: x["cash_flow_score"], reverse=True)
    elif strategy == "growth":
        markets.sort(key=lambda x: x["growth_score"], reverse=True)

    # Create table
    table = Table(title=f"Top {min(top_n, len(markets))} Investment Markets")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Market", style="bold")
    table.add_column("State")
    table.add_column("Overall", justify="right")
    table.add_column("Cash Flow", justify="right")
    table.add_column("Growth", justify="right")
    table.add_column("Median Price", justify="right")
    table.add_column("Median Rent", justify="right")
    table.add_column("Rent/Price", justify="right")

    for i, m in enumerate(markets[:top_n]):
        market = m["market"]
        metrics = m["metrics"]
        table.add_row(
            str(i + 1),
            market.name,
            market.state,
            format_score(metrics.overall_score),
            format_score(metrics.cash_flow_score),
            format_score(metrics.growth_score),
            format_currency(market.median_home_price),
            format_currency(market.median_rent),
            f"{(market.avg_rent_to_price or 0):.2f}%",
        )

    console.print(table)


@app.command()
def analyze(
    city: str = typer.Argument(..., help="City name"),
    state: str = typer.Argument(..., help="State abbreviation"),
    max_price: Optional[float] = typer.Option(
        None,
        "--max-price", "-p",
        help="Maximum property price",
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-l",
        help="Number of properties to analyze",
    ),
):
    """Analyze properties in a specific market."""
    console.print(f"[bold]Analyzing properties in {city}, {state}...[/bold]\n")

    # Get market data
    market_agent = MarketResearchAgent()
    market_id = f"{city.lower().replace(' ', '_')}_{state.lower()}"

    market = asyncio.run(market_agent.get_market(market_id))
    if market:
        console.print(f"[green]Market data found for {market.metro}[/green]")
    else:
        console.print(f"[yellow]No market data for {market_id}, using defaults[/yellow]")

    # Scrape properties
    scraper = MockScraper()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping properties...", total=None)
        result = asyncio.run(scraper.search(
            city=city,
            state=state,
            max_price=max_price,
            limit=limit,
        ))
        progress.update(task, completed=True)

    console.print(f"Found {len(result.properties)} properties\n")

    # Analyze
    deal_agent = DealAnalyzerAgent()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing deals...", total=None)
        analysis = asyncio.run(deal_agent.run(
            properties=result.properties,
            market=market,
            run_sensitivity=True,
        ))
        progress.update(task, completed=True)

    # Display results
    deals = analysis.data["deals"]
    _display_deals_table(deals)

    console.print(f"\n[dim]{analysis.data['passed_filters']}/{analysis.data['total_analyzed']} "
                  f"properties passed filters[/dim]")


@app.command()
def stress_test(
    price: float = typer.Argument(..., help="Purchase price"),
    rent: float = typer.Argument(..., help="Monthly rent"),
    down_payment: float = typer.Option(0.25, "--down", "-d", help="Down payment %"),
    interest_rate: float = typer.Option(0.07, "--rate", "-r", help="Interest rate"),
):
    """Run sensitivity analysis on a hypothetical deal."""
    from src.models.property import Property
    from src.models.deal import Deal

    console.print("[bold]Running stress test...[/bold]\n")

    # Create hypothetical property
    prop = Property(
        id="stress_test",
        address="123 Test St",
        city="Test City",
        state="TX",
        zip_code="12345",
        list_price=price,
        estimated_rent=rent,
        bedrooms=3,
        bathrooms=2,
        source="manual",
    )

    # Create deal
    deal = Deal(id="stress_test_deal", property=prop)
    deal.financials.loan.down_payment_pct = down_payment
    deal.financials.loan.interest_rate = interest_rate
    deal.analyze()

    # Run sensitivity
    analyzer = SensitivityAnalyzer()
    result = analyzer.analyze(deal)

    # Display base case
    console.print(Panel.fit(
        f"[bold]Base Case[/bold]\n"
        f"Purchase Price: {format_currency(price)}\n"
        f"Monthly Rent: {format_currency(rent)}\n"
        f"Down Payment: {format_percent(down_payment)}\n"
        f"Interest Rate: {format_percent(interest_rate)}\n"
        f"\n"
        f"Monthly Cash Flow: [{'green' if result.base_cash_flow > 0 else 'red'}]"
        f"{format_currency(result.base_cash_flow)}[/]\n"
        f"Cash-on-Cash Return: {format_percent(result.base_coc)}\n"
        f"Cap Rate: {format_percent(result.base_cap_rate)}",
        title="Base Case",
        border_style="blue",
    ))

    # Stress scenarios table
    table = Table(title="Stress Test Results")
    table.add_column("Scenario", style="bold")
    table.add_column("Monthly Cash Flow", justify="right")
    table.add_column("Status")

    scenarios = [
        ("Interest Rate +1%", result.rate_increase_1pct_cash_flow),
        ("Interest Rate +2%", result.rate_increase_2pct_cash_flow),
        ("Vacancy 10%", result.vacancy_10pct_cash_flow),
        ("Vacancy 15%", result.vacancy_15pct_cash_flow),
        ("Rent -5%", result.rent_decrease_5pct_cash_flow),
        ("Rent -10%", result.rent_decrease_10pct_cash_flow),
        ("Moderate Stress", result.moderate_stress_cash_flow),
        ("Severe Stress", result.severe_stress_cash_flow),
    ]

    for name, cf in scenarios:
        status = "[green]OK[/green]" if cf >= 0 else "[red]NEGATIVE[/red]"
        table.add_row(
            name,
            format_currency(cf),
            status,
        )

    console.print(table)

    # Risk assessment
    risk_color = {"low": "green", "medium": "yellow", "high": "red"}[result.risk_rating]
    console.print(f"\n[bold]Risk Rating: [{risk_color}]{result.risk_rating.upper()}[/{risk_color}][/bold]")

    if result.break_even_rate:
        console.print(f"Break-even interest rate: {format_percent(result.break_even_rate)}")
    if result.break_even_vacancy:
        console.print(f"Break-even vacancy rate: {format_percent(result.break_even_vacancy)}")
    if result.break_even_rent:
        console.print(f"Break-even rent: {format_currency(result.break_even_rent)}/month")


@app.command()
def version():
    """Show version information."""
    from src import __version__
    console.print(f"Real Estate Deal Platform v{__version__}")


def _display_deals_table(deals: list) -> None:
    """Display deals in a formatted table."""
    if not deals:
        console.print("[yellow]No deals to display[/yellow]")
        return

    table = Table(title=f"Top {len(deals)} Investment Deals")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Address", style="bold", max_width=30)
    table.add_column("City", max_width=15)
    table.add_column("Price", justify="right")
    table.add_column("Rent", justify="right")
    table.add_column("Cash Flow", justify="right")
    table.add_column("CoC", justify="right")
    table.add_column("Cap", justify="right")
    table.add_column("Score", justify="right")

    for deal in deals:
        cf = deal.financial_metrics.monthly_cash_flow if deal.financial_metrics else 0
        cf_style = "green" if cf > 0 else "red"

        table.add_row(
            str(deal.score.rank) if deal.score else "-",
            deal.property.address[:28] + "..." if len(deal.property.address) > 28 else deal.property.address,
            deal.property.city,
            format_currency(deal.property.list_price),
            format_currency(deal.property.estimated_rent),
            f"[{cf_style}]{format_currency(cf)}[/{cf_style}]",
            format_percent(deal.financial_metrics.cash_on_cash_return) if deal.financial_metrics else "N/A",
            format_percent(deal.financial_metrics.cap_rate) if deal.financial_metrics else "N/A",
            format_score(deal.score.overall_score) if deal.score else "N/A",
        )

    console.print(table)

    # Show top deal details
    if deals:
        top = deals[0]
        console.print(f"\n[bold]Top Deal Details:[/bold]")
        console.print(f"  Address: {top.property.full_address}")
        console.print(f"  Property Type: {top.property.property_type.value}")
        console.print(f"  {top.property.bedrooms} bed / {top.property.bathrooms} bath / {top.property.sqft or 'N/A'} sqft")
        console.print(f"  Year Built: {top.property.year_built or 'N/A'}")
        console.print(f"  Days on Market: {top.property.days_on_market}")

        if top.pros:
            console.print(f"\n  [green]Pros:[/green]")
            for pro in top.pros[:3]:
                console.print(f"    + {pro}")

        if top.cons:
            console.print(f"\n  [yellow]Cons:[/yellow]")
            for con in top.cons[:3]:
                console.print(f"    - {con}")

        if top.red_flags:
            console.print(f"\n  [red]Red Flags:[/red]")
            for flag in top.red_flags:
                console.print(f"    ! {flag}")


if __name__ == "__main__":
    app()
