from source.app.databases.database import Get_Connection


class TenantController:

    # ---------------- TENANT ----------------
    @staticmethod
    def AddTenant(ni, first, last, phone, email, occupation, reference):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO Tenant (ni_number, first_name, last_name, phone, email, occupation, tenant_references)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ni, first, last, phone, email, occupation, reference))

        conn.commit()
        conn.close()

    @staticmethod
    def GetTenant(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM Tenant WHERE ni_number = ?", (ni,))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "tenant_id": row[0],
                "ni_number": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "phone": row[4],
                "email": row[5],
                "occupation": row[6],
                "tenant_references": row[7]
            }
        return None

    @staticmethod
    def UpdateTenant(ni, first, last, phone, email, occupation, reference):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        UPDATE Tenant
        SET first_name=?, last_name=?, phone=?, email=?, occupation=?, tenant_references=?
        WHERE ni_number=?
        """, (first, last, phone, email, occupation, reference, ni))

        conn.commit()
        conn.close()

    @staticmethod
    def DeleteTenant(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM Tenant WHERE ni_number=?", (ni,))
        conn.commit()
        conn.close()

    # ---------------- LEASE ----------------
    @staticmethod
    def GetLease(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT l.lease_id, l.apartment_id, l.start_date, l.end_date,
               l.agreed_monthly_rent, l.status
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.ni_number = ?
        """, (ni,))

        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "lease_id": row[0],
                "apartment_id": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "rent": row[4],
                "status": row[5]
            }
        return None

    # ---------------- PAYMENTS ----------------
    @staticmethod
    def GetPayments(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT p.amount, p.payment_date
        FROM Payment p
        JOIN Invoice i ON p.invoice_id = i.invoice_id
        JOIN Lease l ON i.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.ni_number = ?
        """, (ni,))

        rows = cur.fetchall()
        conn.close()

        return [{"amount": r[0], "date": r[1]} for r in rows]

    # ---------------- COMPLAINT ----------------
    @staticmethod
    def AddComplaint(ni, description):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (ni,))
        tenant = cur.fetchone()

        if not tenant:
            raise Exception("Tenant not found")

        cur.execute("""
        INSERT INTO Complaint (tenant_id, description)
        VALUES (?, ?)
        """, (tenant[0], description))

        conn.commit()
        conn.close()

    # ---------------- MAINTENANCE ----------------
    @staticmethod
    def AddMaintenance(ni, apartment_id, issue):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (ni,))
        tenant = cur.fetchone()

        if not tenant:
            raise Exception("Tenant not found")

        cur.execute("""
        INSERT INTO MaintenanceRequest (tenant_id, apartment_id, description, priority)
        VALUES (?, ?, ?, 'MEDIUM')
        """, (tenant[0], apartment_id, issue))

        conn.commit()
        conn.close()

    # ---------------- EARLY TERMINATION ----------------
    @staticmethod
    def TerminateLease(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        # Get lease + rent
        cur.execute("""
        SELECT l.lease_id, l.agreed_monthly_rent
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.ni_number = ?
        """, (ni,))

        lease = cur.fetchone()

        if not lease:
            raise Exception("No lease found")

        lease_id, rent = lease
        penalty = rent * 0.05

        # Update lease
        cur.execute("""
        UPDATE Lease SET status='TERMINATED'
        WHERE lease_id=?
        """, (lease_id,))

        # Create penalty invoice
        cur.execute("""
        INSERT INTO Invoice (lease_id, due_date, amount_due, status)
        VALUES (?, date('now'), ?, 'PENDING')
        """, (lease_id, penalty))

        conn.commit()
        conn.close()

        return penalty