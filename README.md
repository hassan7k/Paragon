# 📘 Paragon Apartment Management System (PAMS)

## Overview
The Paragon Apartment Management System (PAMS) is a desktop-based application developed in Python using Tkinter and SQLite. It is designed to manage tenants, apartments, leases, payments, maintenance requests, and complaints across multiple locations within a centralised system.

The system supports multiple user roles with different access levels, enabling both location-based and organisation-wide operations.

---

## Features

### Core Functionality
- Tenant management (add, search, update, deactivate)
- Apartment management (availability, status updates)
- Lease management (creation, termination, invoice generation)
- Finance system (invoices, payments, revenue tracking)
- Maintenance requests (reporting, scheduling, resolution)
- Complaint management (logging and closing complaints)

### Role-Based Access Control (RBAC)
- **Front Desk**: Manages tenants and day-to-day operations at a single location  
- **Maintenance**: Handles maintenance requests for assigned location  
- **Finance**: Manages invoices, payments, and financial summaries (organisation-wide)  
- **Admin**: Full operational control restricted to their assigned location  
- **Manager**: Full system visibility across all locations  

---

## System Architecture
UI (Tkinter)
↓
Controllers
↓
Services
↓
SQLite Database


- **UI Layer**: Handles user interaction  
- **Controller Layer**: Processes user actions and enforces access rules  
- **Service Layer**: Contains business logic and database interaction  
- **Database Layer**: Stores all system data using SQLite  

---

## Technologies Used

- Python 3.x  
- Tkinter (GUI)  
- SQLite (Database)  
- Git (Version Control)  

---

## Installation & Setup

### 1. Clone the repository

git clone <repo-url>
cd Paragon

### 2. Run the application

py -m source.main

---

## Database Setup (Seed Data)

To initialise the database with test data:

py -m source.app.databases.seed


### Default Test Accounts

| Role        | Username     | Password     | Scope            |
|------------|-------------|-------------|------------------|
| Admin      | admin1      | pass123     | London only      |
| Admin      | admin2      | pass123     | Bristol only     |
| Manager    | manager1    | manager123  | All locations    |
| Finance    | finance1    | pass123     | All locations    |
| Front Desk | frontdesk1  | pass123     | London           |
| Front Desk | frontdesk2  | pass123     | Bristol          |
| Maintenance| maint1      | pass123     | London           |

---

## Multi-Location Behaviour

- **Admins** are restricted to their assigned location  
- **Managers** have access to all locations  
- **Finance users** can view financial data across all locations  
- Data relationships are enforced via:

Tenant → Lease → Apartment → Location

---

## ▶️ How to Demo the System

Follow this order for a clean demonstration:

### 1. Front Desk (Operational Flow)
Login:

frontdesk1 / pass123


Demonstrate:
- Add or view tenants  
- View apartments  
- Create a lease  
- Confirm apartment becomes occupied  

---

### 2. Finance (Billing Flow)
Login:

finance1 / pass123


Demonstrate:
- View all invoices  
- Search invoice by ID or tenant  
- View payment records  
- Calculate totals / revenue  

---

### 3. Maintenance (Support Flow)
Login:

maint1 / pass123


Demonstrate:
- View maintenance requests  
- Resolve a request  
- Update status  

---

### 4. Complaints (Tenant Issues)
Use any operational role:

Demonstrate:
- Add complaint  
- View complaint  
- Close complaint  

---

### 5. Admin (Location-Based Control)
Login (London):

admin1 / pass123

Demonstrate:
- Only London data is visible  
- Tenant list is filtered by location  
- Apartments limited to London  
- Leases limited to London  

Login (Bristol):

admin2 / pass123

Demonstrate:
- Same views but for Bristol only  

---

### 6. Manager (Global Oversight)
Login:

manager1 / manager123

Demonstrate:
- All locations visible  
- Compare tenants across locations  
- View all apartments  
- View all financial data  
- Access full reporting  

---

## Current Status

The system is functional with integrated modules for:
- tenant lifecycle  
- lease and billing  
- maintenance and complaints  
- role-based access control  
- multi-location data handling  

Further refinements are ongoing, including UI consistency and extended validation.

---

## Notes

- The system uses a local SQLite database (`paragondata.db`)  
- If login or data issues occur, delete the database and reseed  
- The application is designed for desktop use  

---

## Authors

Hassan Omar, Cem Basogukl, Neha Neha, Michael Myint, Aye Mon Thiri

Developed as part of a Systems Development Group Project.