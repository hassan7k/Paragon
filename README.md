# Paragon Apartment Management System (PAMS)

**UFCF8S-30-2 Advanced Software Development — Group Project**
University of the West of England, Bristol

---

## Team

| Member | Module |
|--------|--------|
| Cem Basogul | **Admin + Manager** (this repo) |
| Michael | Front Desk (TenantUI) |
| Neha | Finance (FinanceUI) |
| Rena | Maintenance (MaintenanceUI) |

---

## Module Overview (Cem)

This repository contains the **Admin and Manager module** of PAMS, built on a full layered architecture:

- **Database layer** — SQLite with 9 tables, FK constraints, SHA-256 + salt password hashing
- **Service layer** — validation, business logic, atomic transactions
- **Controller layer** — RBAC-enforced API between UI and services
- **UI layer** — dark-themed Tkinter dashboard with 8 tabs

### RBAC Design

| Role | Scope |
|------|-------|
| `ADMIN` | Full access scoped to their assigned location only |
| `MANAGER` | Full system access across all locations + city expansion |

Security enforced at **three levels**:
1. Login — deactivated accounts (`is_active = 0`) are blocked at authentication
2. Read/list — all queries filtered by `location_id` for ADMIN
3. Action — ownership checks before any mutation (terminate lease, close complaint, deactivate staff, update apartment status)

---

## Project Structure

```
PAMS/
├── main.py                          # Entry point — creates tables, seeds DB, launches UI
├── requirements.txt
├── source/
│   └── app/
│       ├── databases/
│       │   ├── database.py          # SQLite schema & connection (9 tables)
│       │   └── seed.py              # Default locations, users, apartments
│       ├── services/
│       │   ├── GlobalFunctions.py   # NI, phone, email validation + password hashing
│       │   ├── AuthService.py       # Login (checks is_active), CreateUser
│       │   ├── TenantService.py     # Add, Update, DeactivateTenant (soft-delete)
│       │   ├── ApartmentService.py
│       │   ├── LeaseService.py      # CreateLease, TerminateLease (date guard), TerminateLeaseEarly
│       │   ├── InvoiceService.py
│       │   ├── PaymentService.py
│       │   ├── MaintenanceService.py
│       │   ├── ComplaintService.py
│       │   └── ReportingService.py  # All methods accept LocationId=None (Manager) or int (Admin)
│       ├── controllers/
│       │   ├── Auth.py              # Shared auth controller
│       │   ├── AdminController.py   # Cem's controller — full RBAC + ownership checks
│       │   ├── Tenants.py
│       │   ├── Apartments.py
│       │   ├── Payments.py
│       │   ├── Maintenance.py
│       │   ├── Complaints.py
│       │   └── Reports.py
│       ├── ui/
│       │   ├── LoginUI.py           # Login screen (routes by role)
│       │   ├── AdminUI.py           # Cem's 8-tab dashboard
│       │   ├── TenantUI.py          # Michael's module
│       │   ├── FinanceUI.py         # Neha's module
│       │   └── MaintenanceUI.py     # Rena's module
│       └── tests/
│           ├── auth_testing.py
│           ├── tenant_testing.py
│           ├── apartment_testing.py
│           ├── lease_testing.py
│           ├── invoice_testing.py
│           ├── payment_testing.py
│           ├── maintenance_testing.py
│           ├── complaint_testing.py
│           └── report_testing.py
```

---

## How to Run

**Requirements:** Python 3.10+, Tkinter (included with standard Python). No external packages needed.

```bash
# From the PAMS/ directory:
python main.py
```

The SQLite database is created automatically on first run and seeded with sample data.

---

## Default Login Credentials

| Username | Password | Role | Location |
|----------|----------|------|----------|
| `manager` | `Manager123` | MANAGER | All locations |
| `admin1` | `Admin123` | ADMIN | Bristol |
| `admin2` | `Admin123` | ADMIN | Cardiff |
| `front1` | `Front123` | FRONT_DESK | Bristol |
| `finance1` | `Finance123` | FINANCE | Bristol |
| `maint1` | `Maint123` | MAINTENANCE | Bristol |

---

## Admin / Manager Dashboard — 8 Tabs

| # | Tab | Description | ADMIN | MANAGER |
|---|-----|-------------|-------|---------|
| 1 | **Dashboard** | 12 metric cards: occupancy, rent collected/pending, maintenance cost, avg resolution days, open/closed complaints | Own location | All locations |
| 2 | **Tenants** | Add new tenant · Edit contact details (inline pre-fill on row select) · Deactivate (soft-delete, blocked if active lease exists) | Own location only | All tenants |
| 3 | **Leases** | Create lease with initial invoice · Standard Terminate (past end-date only) · Early Terminate (30-day notice + 5% penalty invoice) | Own location only | All leases |
| 4 | **Apartments** | Add apartment · Update status (AVAILABLE / MAINTENANCE) | Own location only | All locations |
| 5 | **Invoices** | Full invoice history with PAID / PENDING / OVERDUE colour coding + summary counts | Own location only | All locations |
| 6 | **Complaints** | View complaints · Close complaint | Own location only | All locations |
| 7 | **Staff** | Create account (ADMIN: own location only, cannot create ADMIN/MANAGER) · Deactivate (soft-delete) | Own location only | All staff |
| 8 | **Locations** | View all cities · Add new city | — | Manager only |

---

## Key Business Rules

- **Early lease termination** — tenant must give ≥ 30 days notice; a 5% monthly-rent penalty invoice is generated automatically
- **Standard termination** — only permitted on or after the lease natural end date; earlier attempts are rejected with a clear error
- **Tenant soft-delete** — sets `is_active = 0`; all lease, invoice, and complaint history is preserved
- **Staff soft-delete** — sets `is_active = 0`; deactivated accounts cannot log in
- **Admin create staff** — Admin can only create FRONT_DESK / FINANCE / MAINTENANCE accounts for their own location; MANAGER accounts require a Manager login

---

## Running Tests

Each test module is standalone and resets the database before running:

```bash
python -m source.app.tests.auth_testing
python -m source.app.tests.tenant_testing
python -m source.app.tests.apartment_testing
python -m source.app.tests.lease_testing
python -m source.app.tests.invoice_testing
python -m source.app.tests.payment_testing
python -m source.app.tests.maintenance_testing
python -m source.app.tests.complaint_testing
python -m source.app.tests.report_testing
```

**All 30 tests pass.**

---

## Database Schema

SQLite with 9 tables and FK enforcement:

```
Location → Users (is_active)
         → Apartment → Lease → Invoice → Payment
                     → MaintenanceRequest
Tenant (is_active) → Lease
                   → Complaint
```

Key design decisions:
- SHA-256 password hashing with random per-user salt
- UK NI number validation (format: AB123456C)
- UK phone validation (11 digits, starts with 0)
- Foreign key constraints enforced via PRAGMA foreign_keys = ON
- Soft-delete on both Users and Tenant tables (is_active flag)
- All reporting queries parameterised with LocationId=None (Manager) vs int (Admin)
