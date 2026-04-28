plans = [
    {
        "name": "Free",
        "description": "Get started for free. Perfect for individuals or testing the platform before committing.",
        "amount": 0.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Free",
        "packages": [
            {"name": "Reports", "count": 2, "tag": "reports", "is_unlimited": False},
            {
                "name": "Team Members",
                "count": 2,
                "tag": "team_members",
                "is_unlimited": False,
            },
            {
                "name": "Site Inspections",
                "count": 5,
                "tag": "site_inspections",
                "is_unlimited": False,
            },
        ],
    },
    {
        "name": "Basic",
        "description": "For independent contractors and small teams managing a handful of active builds.",
        "amount": 10000.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Paid",
        "packages": [
            {"name": "Reports", "count": 5, "tag": "reports", "is_unlimited": False},
            {
                "name": "Team Members",
                "count": 5,
                "tag": "team_members",
                "is_unlimited": False,
            },
            {
                "name": "Site Inspections",
                "count": 10,
                "tag": "site_inspections",
                "is_unlimited": False,
            },
        ],
    },
    {
        "name": "Pro",
        "description": "For growing construction firms running multiple concurrent projects with larger site teams.",
        "amount": 25000.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Paid",
        "packages": [
            {"name": "Reports", "count": 10, "tag": "reports", "is_unlimited": True},
            {
                "name": "Team Members",
                "count": 20,
                "tag": "team_members",
                "is_unlimited": False,
            },
            {
                "name": "Site Inspections",
                "count": 20,
                "tag": "site_inspections",
                "is_unlimited": True,
            },
        ],
    },
    {
        "name": "Enterprise",
        "description": "For large construction companies and real estate developers managing large-scale builds across multiple sites.",
        "amount": 60000.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Paid",
        "packages": [
            {"name": "Reports", "count": 0, "tag": "reports", "is_unlimited": True},
            {
                "name": "Team Members",
                "count": 0,
                "tag": "team_members",
                "is_unlimited": True,
            },
            {
                "name": "Site Inspections",
                "count": 0,
                "tag": "site_inspections",
                "is_unlimited": True,
            },
        ],
    },
]


plans = [
    {
        "name": "Free",
        "description": "Ideal for small teams or testing the PMS app.",
        "amount": 0.0,
        "currency": "NGN",
        "frequency": "Monthly",
        "plan_status": "Free",
        "packages": [
            {
                "name": "Reports",
                "count": 3,
                "tag": "reports",
                "is_unlimited": False,
            },  # 500MB
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
            {"name": "Reports", "count": 0, "tag": "reports", "is_unlimited": True},
        ],
    },
]
