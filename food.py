"""
routes/food.py
--------------
Food-related routes:
  - POST /food/add         → donate a food item
  - GET  /food/listings    → view all available food
  - POST /food/request/<id> → claim/request a food listing
  - GET  /food/my-donations → view user's own donations
  - POST /food/handle-request/<req_id> → approve/reject a request (donor only)
  - GET  /food/my-requests  → view the user's own requests
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from database.models import db, FoodListing, FoodRequest

food_bp = Blueprint("food", __name__)


# ── Add Food Donation ─────────────────────────────────────────────────────────
@food_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_food():
    """Render the 'Add Food' form (GET) or save the donation (POST)."""
    if request.method == "POST":
        food_name    = request.form.get("food_name", "").strip()
        quantity     = request.form.get("quantity", "").strip()
        location     = request.form.get("location", "").strip()
        description  = request.form.get("description", "").strip()
        category     = request.form.get("category", "").strip()
        expiry_str   = request.form.get("expiry_time", "").strip()

        # ── Validate required fields ──────────────────────────────────────────
        if not food_name or not quantity or not location or not expiry_str:
            flash("Food name, quantity, location, and expiry time are required.", "danger")
            return render_template("add_food.html")

        # ── Parse expiry datetime ─────────────────────────────────────────────
        try:
            expiry_time = datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid expiry date/time format.", "danger")
            return render_template("add_food.html")

        if expiry_time <= datetime.utcnow():
            flash("Expiry time must be in the future.", "danger")
            return render_template("add_food.html")

        # ── Save to database ──────────────────────────────────────────────────
        listing = FoodListing(
            food_name   = food_name,
            quantity    = quantity,
            location    = location,
            description = description,
            category    = category,
            expiry_time = expiry_time,
            donor_id    = current_user.id,
        )
        db.session.add(listing)
        db.session.commit()

        flash(f"'{food_name}' has been listed successfully! 🙏", "success")
        return redirect(url_for("food.my_donations"))

    return render_template("add_food.html")


# ── View Available Listings ───────────────────────────────────────────────────
@food_bp.route("/listings")
def listings():
    """Show all currently available (non-expired, non-claimed) food items."""
    now = datetime.utcnow()

    # Optional location-based filter
    loc_filter = request.args.get("location", "").strip()
    # Optional category filter
    cat_filter = request.args.get("category", "").strip()

    query = FoodListing.query.filter(
        FoodListing.status      == "available",
        FoodListing.expiry_time >  now,
    )

    if loc_filter:
        query = query.filter(FoodListing.location.ilike(f"%{loc_filter}%"))

    if cat_filter:
        query = query.filter(FoodListing.category == cat_filter)

    foods = query.order_by(FoodListing.expiry_time.asc()).all()

    # Collect distinct categories for the filter dropdown
    categories = db.session.query(FoodListing.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template(
        "listings.html",
        foods      = foods,
        loc_filter = loc_filter,
        cat_filter = cat_filter,
        categories = categories,
        now        = now,
    )


# ── Request / Claim a Food Listing ───────────────────────────────────────────
@food_bp.route("/request/<int:food_id>", methods=["POST"])
@login_required
def request_food(food_id: int):
    """Create a FoodRequest record claiming a specific listing."""
    listing = FoodListing.query.get_or_404(food_id)

    # Prevent donor from claiming their own donation
    if listing.donor_id == current_user.id:
        flash("You cannot claim your own donation.", "warning")
        return redirect(url_for("food.listings"))

    # Prevent duplicate requests
    existing = FoodRequest.query.filter_by(
        food_id=food_id, requester_id=current_user.id
    ).first()
    if existing:
        flash("You have already requested this item.", "info")
        return redirect(url_for("food.listings"))

    if listing.status != "available":
        flash("This item is no longer available.", "warning")
        return redirect(url_for("food.listings"))

    message = request.form.get("message", "").strip()

    req = FoodRequest(
        food_id      = food_id,
        requester_id = current_user.id,
        message      = message,
    )
    db.session.add(req)
    db.session.commit()

    flash("Your request has been submitted! The donor will confirm shortly.", "success")
    return redirect(url_for("food.my_requests"))


# ── My Donations ──────────────────────────────────────────────────────────────
@food_bp.route("/my-donations")
@login_required
def my_donations():
    """Show the logged-in user's donations and incoming requests on them."""
    donations = FoodListing.query.filter_by(donor_id=current_user.id)\
                                 .order_by(FoodListing.created_at.desc()).all()
    return render_template("my_donations.html", donations=donations, now=datetime.utcnow())


# ── Handle (Approve/Reject) a Request ────────────────────────────────────────
@food_bp.route("/handle-request/<int:req_id>", methods=["POST"])
@login_required
def handle_request(req_id: int):
    """Donor approves or rejects a pending food request."""
    food_req = FoodRequest.query.get_or_404(req_id)

    # Only the donor of the listing can act on the request
    if food_req.food_listing.donor_id != current_user.id:
        abort(403)

    action = request.form.get("action")   # "approve" or "reject"

    if action == "approve":
        food_req.status               = "approved"
        food_req.food_listing.status  = "claimed"   # mark the listing as claimed
        # Reject all other pending requests for same listing
        others = FoodRequest.query.filter(
            FoodRequest.food_id == food_req.food_id,
            FoodRequest.id      != req_id,
            FoodRequest.status  == "pending",
        ).all()
        for other in others:
            other.status = "rejected"
        flash("Request approved and listing marked as claimed. ✅", "success")

    elif action == "reject":
        food_req.status = "rejected"
        flash("Request rejected.", "info")

    db.session.commit()
    return redirect(url_for("food.my_donations"))


# ── My Requests ───────────────────────────────────────────────────────────────
@food_bp.route("/my-requests")
@login_required
def my_requests():
    """Show all food requests submitted by the current user."""
    reqs = FoodRequest.query.filter_by(requester_id=current_user.id)\
                            .order_by(FoodRequest.requested_at.desc()).all()
    return render_template("my_requests.html", requests=reqs)
