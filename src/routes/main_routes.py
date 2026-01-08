"""Main application routes."""
from flask import Blueprint, render_template
from flask_login import login_required
from src.rcon_client import get_online_players
from src.services.item_service import build_item_catalog
from src.services.location_service import fetch_locations
from src.commands import VILLAGE_TYPES
from src.config_loader import get_kits, get_quick_commands

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    """Main dashboard page."""
    players = get_online_players()
    kits_config = get_kits()
    quick_commands = get_quick_commands()
    
    return render_template(
        "dashboard.html",
        players=players,
        items=build_item_catalog(),
        village_types=VILLAGE_TYPES,
        locations=fetch_locations(),
        kits=kits_config.get("kits", []),
        quick_commands=quick_commands if isinstance(quick_commands, list) else [],
    )


@main_bp.route('/diagnostics')
@login_required
def diagnostics():
    """RCON diagnostics page."""
    return render_template("diagnostics.html")


@main_bp.route('/error-logs')
@login_required
def error_logs_page():
    """Dedicated error logs page."""
    return render_template("error_logs.html")


@main_bp.route('/player')
@login_required
def player():
    """Player management page."""
    players = get_online_players()
    return render_template("player.html", players=players)
