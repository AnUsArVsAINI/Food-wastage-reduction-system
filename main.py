"""
routes/main.py
--------------
General-purpose routes: home page and dashboard.
"""

from datetime import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from database.models import FoodListing, FoodRequest, User

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Landing page with statistics."""
    total_listings = FoodListing.query.count()
    available      = FoodListing.query.filter_by(status="available").count()
    claimed        = FoodListing.query.filter_by(status="claimed").count()
    recent         = FoodListing.query.filter(
                         FoodListing.status      == "available",
                         FoodListing.expiry_time  > datetime.utcnow(),
                     ).order_by(FoodListing.created_at.desc()).limit(6).all()
    return render_template(
        "home.html",
        total_listings = total_listings,
        available      = available,
        claimed        = claimed,
        recent         = recent,
        now            = datetime.utcnow(),
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """User dashboard summarising their activity."""
    now = datetime.utcnow()

    my_donations  = FoodListing.query.filter_by(donor_id=current_user.id).count()
    my_requests   = FoodRequest.query.filter_by(requester_id=current_user.id).count()
    pending_reqs  = FoodRequest.query.join(FoodListing).filter(
                        FoodListing.donor_id == current_user.id,
                        FoodRequest.status   == "pending",
                    ).count()
    active_listings = FoodListing.query.filter(
                          FoodListing.donor_id    == current_user.id,
                          FoodListing.status      == "available",
                          FoodListing.expiry_time  > now,
                      ).all()
    recent_requests = FoodRequest.query.filter_by(requester_id=current_user.id)\
                                       .order_by(FoodRequest.requested_at.desc())\
                                       .limit(5).all()

    return render_template(
        "dashboard.html",
        my_donations    = my_donations,
        my_requests     = my_requests,
        pending_reqs    = pending_reqs,
        active_listings = active_listings,
        recent_requests = recent_requests,
        now             = now,
    )


@main_bp.route("/admin")
def admin():
    """Read-only admin panel – shows every row in all three tables."""
    return render_template(
        "admin.html",
        users    = User.query.order_by(User.id).all(),
        listings = FoodListing.query.order_by(FoodListing.id).all(),
        requests = FoodRequest.query.order_by(FoodRequest.id).all(),
    )
