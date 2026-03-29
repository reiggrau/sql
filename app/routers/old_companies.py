"""This module defines the API endpoints for company-related operations."""

from fastapi import APIRouter, HTTPException
from app.db.connection import fetch_one, fetch_all

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", summary="Get all companies")
def get_companies() -> list[dict]:
    """Get all companies."""
    sql = """--sql
    SELECT * FROM companies;
    """
    return fetch_all(sql)


@router.get("/employees", summary="Companies sorted by number of employees")
def get_companies_by_employee_count() -> list[dict]:
    """Get companies sorted by the number of employees."""
    sql = """--sql
        SELECT c.id, c.name, COUNT(u.id) AS employee_count
        FROM companies c
        LEFT JOIN users u ON c.id = u.company_id
        GROUP BY c.id, c.name -- Group by company ID and name to get employee count per company
        ORDER BY employee_count DESC, c.name ASC; -- Sort by employee count descending, then by company name ascending
    """
    return fetch_all(sql)


@router.get("/top-2-applied-companies", summary="Top 2 companies by applications (all clauses)")
def top_companies() -> list[dict]:
    """Find the top 2 companies that have received more than 1 application,
    showing how many were accepted, excluding Biotech companies."""
    sql = """--sql
        SELECT
            c.name AS company,
            c.industry,
            COUNT(a.id) AS total_applications,
            SUM(CASE WHEN a.status = 'accepted' THEN 1 ELSE 0 END) AS accepted
        FROM applications a
        JOIN companies c ON a.company_id = c.id
        WHERE c.industry != 'Biotech'
        GROUP BY c.id, c.name, c.industry
        HAVING COUNT(a.id) > 1
        ORDER BY total_applications DESC
        LIMIT 2;
    """
    return fetch_all(sql)


@router.get("/{company_id}", summary="Get company by id")
def get_company(company_id: int) -> dict | None:
    """Get a company by its ID."""
    sql = """--sql
    SELECT * FROM companies WHERE id = %s;
    """
    company = fetch_one(sql, (company_id,))
    if company is None:
        raise HTTPException(
            status_code=404, detail=f"Company {company_id} not found")
    return company


@router.get("/{company_id}/users", summary="Get users by company id")
def get_users_by_company(company_id: int) -> list[dict]:
    """Get all users for a specific company."""
    company = get_company(company_id)  # Check if the company exists
    if company is None:
        raise HTTPException(
            status_code=404, detail=f"Company {company_id} not found")
    sql = """--sql
    SELECT * FROM users WHERE company_id = %s;
    """
    return fetch_all(sql, (company_id,))
