import click

from dependency_injector.wiring import inject, Provide
from sqlalchemy.orm import sessionmaker

from py_reportit.shared.config.container import Container
from py_reportit.shared.config import config
from py_reportit.shared.model.user import User
from py_reportit.shared.repository.user import UserRepository


@click.group()
def utils():
  pass

@click.command()
@click.option(
    "--username",
    prompt="Desired username",
    type=click.STRING,
    help="The username for the new admin account."
)
@click.option(
    "--password",
    prompt="Desired password",
    type=click.STRING,
    help="The password for the new admin account.",

)
@inject
def create_admin_account(
    username: str,
    password: str,
    user_repository: UserRepository = Provide[Container.user_repository],
    session_maker: sessionmaker = Provide[Container.sessionmaker]
):
    """Simple function to create a new admin account for the REST API."""
    click.echo(f"Adding new admin user with username {username} ...")

    with session_maker() as session:
        new_admin_user = User(username=username, password=password, admin=True)
        user_repository.create(session, new_admin_user)
        session.commit()

    click.echo("Done!")

@click.command()
@click.option(
    "--username",
    prompt="Target username",
    type=click.STRING,
    help="The username of the user to be deleted."
)
@inject
def delete_account(
    username: str,
    user_repository: UserRepository = Provide[Container.user_repository],
    session_maker: sessionmaker = Provide[Container.sessionmaker]
):
    """Simple function to delete an account for the REST API."""
    click.echo(f"Deleting user with username {username} ...")

    with session_maker() as session:
        user_repository.delete_by_username(session, username)
        session.commit()

    click.echo("Done!")

utils.add_command(create_admin_account)
utils.add_command(delete_account)

container = Container()

container.config.from_dict(config)

container.wire(modules=[__name__])

if __name__ == "__main__":
    utils()
