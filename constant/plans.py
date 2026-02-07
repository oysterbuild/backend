plans = [
    {
        "name": "Free",
        "description": "Ideal for small teams or testing the PMS app.",
        "amount": 0.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Free",
        "packages": [
            {"name": "Projects", "count": 1, "tag": "projects", "is_unlimited": False},
            {"name": "Reports", "count": 10, "tag": "reports", "is_unlimited": False},
            {
                "name": "Storage (KB)",
                "count": 500_000,
                "tag": "storage",
                "is_unlimited": False,
            },  # 500MB
            {
                "name": "Team Members",
                "count": 1,
                "tag": "team_members",
                "is_unlimited": False,
            },
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
            {"name": "Projects", "count": 5, "tag": "projects", "is_unlimited": False},
            {"name": "Reports", "count": 100, "tag": "reports", "is_unlimited": False},
            {
                "name": "Storage (KB)",
                "count": 5_000_000,
                "tag": "storage",
                "is_unlimited": False,
            },  # 5GB
            {
                "name": "Team Members",
                "count": 5,
                "tag": "team_members",
                "is_unlimited": False,
            },
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
            {"name": "Projects", "count": 20, "tag": "projects", "is_unlimited": False},
            {"name": "Reports", "count": 500, "tag": "reports", "is_unlimited": False},
            {
                "name": "Storage (KB)",
                "count": 25_000_000,
                "tag": "storage",
                "is_unlimited": False,
            },  # 25GB
            {
                "name": "Team Members",
                "count": 20,
                "tag": "team_members",
                "is_unlimited": False,
            },
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
            {
                "name": "Projects",
                "count": None,
                "tag": "projects",
                "is_unlimited": True,
            },
            {"name": "Reports", "count": None, "tag": "reports", "is_unlimited": True},
            {
                "name": "Storage (KB)",
                "count": None,
                "tag": "storage",
                "is_unlimited": True,
            },
            {
                "name": "Team Members",
                "count": None,
                "tag": "team_members",
                "is_unlimited": True,
            },
        ],
    },
]
