from models.plans import Plan, Package
from constant.plans import plans
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db_setup import get_database
from fastapi import Depends
from sqlalchemy import select
from constant.roles_permissions import default_role_permissions
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.loggers import setup_logger
from helpers.slugify import generate_slug

logger = setup_logger("Load_Plan")


class PlansService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_plans(self):
        logger.info("🔹 Seeding plans")
        for plan_data in plans:
            name = f"{plan_data['name']} {plan_data['frequency']}"
            slug = generate_slug(name)
            stmt = select(Plan).where(Plan.slug == slug)
            plan = await self.db.scalar(stmt)

            if plan:
                logger.info(f"⚠️ Plan already exists: {plan_data['name']}")
                continue

            plan = Plan(
                name=plan_data["name"],
                description=plan_data["description"],
                frequency=plan_data["frequency"],
                plan_status=plan_data["plan_status"],
                amount=plan_data["amount"],
                slug=slug,
                currency=plan_data.get("currency", "NGN"),
            )
            self.db.add(plan)
            await self.db.flush()  # get plan.id for packages
            logger.info(f"✅ Plan created: {plan.name}")

            # Add packages
            for pkg in plan_data["packages"]:
                pkg_stmt = select(Package).where(
                    Package.plan_id == plan.id, Package.tag == pkg["tag"]
                )
                existing_pkg = await self.db.scalar(pkg_stmt)
                if existing_pkg:
                    logger.info(
                        f"⚠️ Package already exists for plan {plan.name}: {pkg['name']}"
                    )
                    continue

                self.db.add(
                    Package(
                        plan_id=plan.id,
                        name=pkg["name"],
                        count=pkg["count"],
                        tag=pkg["tag"],
                        is_unlimited=pkg["is_unlimited"],
                    )
                )
                logger.info(f"🔹 Package added: {pkg['name']} → {plan.name}")

        await self.db.commit()
        logger.info("✅ All plans & packages seeded successfully")


# -----------------------------
# Runner function
# -----------------------------
async def seed_plans():
    async for db in get_database():
        loader = PlansService(db=db)
        try:
            logger.info("🔹 Starting plans seeding")
            await loader.add_plans()
        except Exception as e:
            logger.error(f"❌ Error seeding plans: {e}")
            await db.rollback()
        finally:
            await db.close()
            logger.info("🔹 DB session closed")
