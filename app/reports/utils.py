# app/reports/utils.py
import pandas as pd
from ..models import LeaveRequest

def generate_report_df(filter_by=None):
    """
    Return a pandas DataFrame of leave requests.
    filter_by: dict with optional keys - employee_id, status, month
    """
    query = LeaveRequest.query

    if filter_by:
        if "employee_id" in filter_by:
            query = query.filter(LeaveRequest.employee_id == filter_by["employee_id"])
        if "status" in filter_by:
            query = query.filter(LeaveRequest.status == filter_by["status"])
        if "month" in filter_by:
            month = filter_by["month"]
            query = query.filter(LeaveRequest.start_date.between(month.start, month.end))

    data = []
    for leave in query.all():
        data.append({
            "ID": leave.id,
            "Employee": leave.employee.name,
            "Start Date": leave.start_date,
            "End Date": leave.end_date,
            "Type": leave.leave_type,
            "Status": leave.status,
            "Manager": leave.manager.name if leave.manager else "N/A",
            "Manager Comment": leave.manager_comment or "",
        })

    df = pd.DataFrame(data)
    return df