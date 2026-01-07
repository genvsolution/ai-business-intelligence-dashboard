from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from functools import wraps

# Assume these models and forms exist in their respective modules
# For a real project, these imports would point to their actual locations,
# e.g., from app.models.lead import Lead, from app.forms.lead_forms import LeadForm
from app.models import db, Lead, User, Task, ActivityLog
from app.forms.leads import LeadForm, TaskForm, ActivityLogForm, LeadStatusForm

# --- RBAC Decorator (Placeholder/Simplified) ---
# In a full project, this decorator would likely reside in a separate `app.decorators` module
# and integrate with a more robust RBAC system (e.g., checking specific permissions
# like 'leads:create', 'leads:edit_own', 'leads:edit_all' rather than just roles directly).
# For this exercise, we assume current_user has a 'roles' attribute (list of Role objects)
# and Role objects have a 'name' attribute (e.g., 'Admin', 'Sales Manager', 'Sales Representative').

def permission_required(roles=None):
    """
    Decorator to check if the current user has any of the specified roles.
    If roles is None or empty, it implies general authenticated access without specific role checks.
    
