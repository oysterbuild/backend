plans = [
    {
        "name": "Free",
        "description": "Ideal for small teams or testing the PMS app.",
        "amount": 0.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Free",
        "packages": [
  
            {"name": "Reports", "count": 3, "tag": "reports", "is_unlimited": False},# 500MB
 
        ],
    },
    {
        "name": "Basic",
        "description": "Small teams with moderate usage of PMS features.",
        "amount": 10000.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Paid",
        "packages": [

            {"name": "Reports", "count": 10, "tag": "reports", "is_unlimited": False},

        ],
    },
    {
        "name": "Pro",
        "description": "For growing teams managing multiple projects efficiently.",
        "amount": 20000.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Paid",
        "packages": [

            {"name": "Reports", "count": 15, "tag": "reports", "is_unlimited": False},
        ],
    },
    {
        "name": "Enterprise",
        "description": "Custom plan for large organizations with unlimited usage.",
        "amount": 50000.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Paid",
        "packages": [
            {"name": "Reports", "count": None, "tag": "reports", "is_unlimited": True},
        ],
    },
]
