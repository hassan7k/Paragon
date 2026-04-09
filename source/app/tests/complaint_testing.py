import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from source.app.databases.database import DatabasePath, Create_Tables
from source.app.services.TenantService import TenantService
from source.app.services.ComplaintService import ComplaintService

def ResetDatabase():
    if os.path.exists(DatabasePath):
        os.remove(DatabasePath)

def Execute():

    print("Running ComplaintService testing...")

    ResetDatabase()
    Create_Tables()

    TenantId = TenantService.AddTenant(
        "AY123456C",
        "John",
        "Doe",
        "07123456789",
        "john.doe@example.co.uk",
        "Student",
        "Ref"
    )

    print("All set up.")
    print(f"TenantId={TenantId}")
    print()

    ComplaintId = None

    try:
        ComplaintId = ComplaintService.CreateComplaint(
            TenantId,
            "Noise complaint about neighbours."
        )

        print(f"Pass. Complaint created with ID: {ComplaintId}")

    except Exception as FailError:
        print(f"Fail. Complaint creation raised error: {FailError}")

    try:
        ComplaintService.CreateComplaint(
            999999,
            "Test complaint"
        )

        print("Fail. Should fail due to invalid tenant.")

    except Exception as FailError:
        print(f"Pass. Invalid tenant failed correctly: {FailError}")

    # Update status
    try:
        ComplaintService.UpdateComplaintStatus(ComplaintId, "CLOSED")

        Complaint = ComplaintService.GetComplaintById(ComplaintId)

        if Complaint[3] == "CLOSED":
            print("Pass. Complaint status updated correctly.")
        else:
            print("Fail. Complaint status not updated.")

    except Exception as FailError:
        print(f"Fail. Updating complaint status raised error: {FailError}")

    try:
        ComplaintService.CloseComplaint(ComplaintId)

        Complaint = ComplaintService.GetComplaintById(ComplaintId)

        if Complaint[3] == "CLOSED":
            print("Pass. Complaint closed correctly.")
        else:
            print("Fail. Complaint should be CLOSED.")

    except Exception as FailError:
        print(f"Fail. Closing complaint raised error: {FailError}")

    try:
        Complaints = ComplaintService.GetComplaintsByTenant(TenantId)

        if len(Complaints) >= 1:
            print(f"Pass. Complaints retrieved correctly. Count: {len(Complaints)}")
        else:
            print("Fail. Expected complaints for this tenant.")

    except Exception as FailError:
        print(f"Fail. Retrieving complaints raised error: {FailError}")


if __name__ == "__main__":
    Execute()
