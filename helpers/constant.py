from dateutil.relativedelta import relativedelta
from datetime import datetime
import string


def get_next_cycle_date(
    last_cycle_date: datetime, frequency: string, num=1
) -> datetime:
    due_date = None

    if frequency == "Monthly":
        due_date = last_cycle_date + relativedelta(months=num)
    elif frequency == "Yearly":
        due_date = last_cycle_date + relativedelta(years=num)
    elif frequency == "Daily":
        due_date = last_cycle_date + relativedelta(days=+1)
    elif frequency == "Weekly":
        due_date = last_cycle_date + relativedelta(weeks=+1)
    elif frequency == "Quarterly":
        due_date = last_cycle_date + relativedelta(months=+3)

    return due_date
