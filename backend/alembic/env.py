from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
from app.modules.customers import model as customers_model  # noqa: F401
from app.modules.finance import model as finance_model  # noqa: F401
from app.modules.inventory import model as inventory_model  # noqa: F401
from app.modules.print_templates import model as print_templates_model  # noqa: F401
from app.modules.products import model as products_model  # noqa: F401
from app.modules.purchase import model as purchase_model  # noqa: F401
from app.modules.sales import model as sales_model  # noqa: F401
from app.modules.suppliers import model as suppliers_model  # noqa: F401
from app.modules.users import model as users_model  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
