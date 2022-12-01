import typer
import json

from ..connections import get_db_session
from ..models import Account, Group
from ..settings import logger

app = typer.Typer(name="account", help="Various utilities for working with accounts")


# class ArgumentValidations:
#     @staticmethod
#     def is_valid_status(val):
#         ivalue = int(value)
#         if ivalue <= 0:
#             raise TypeError(f"{value} is an invalid positive int value")
#         return value

#     @staticmethod
#     def is_valid_quota(val):
#         course = str(course)
#         if len(course) > 8 or len(course) < 7:
#             raise TypeError(f"{course} must be under 7 or 8 characters")
#         if not course[0:3].isalpha():
#             raise TypeError(f"First three characters of {course} must be letters")
#         if not course[3:7].isnumeric():
#             raise TypeError(f"Next four characters of {course} must be numbers")
#         return course

#     @staticmethod
#     def is_valid_group(val):
#         if course is None:
#             return course
#         if len(str(course)) > 3:
#             raise TypeError(f"Extension must be three or less characters long")
#         return course

ARG_TO_STATUS = {
    "disabled": "DISABLED",
    "personal": "USING_PERSONAL_QUOTA",
    "group": "USING_GROUP_QUOTA",
}


@app.command()
def create(
    username: str,
    status: str = typer.Option("personal", "--status"),
    quota: int = typer.Option(0, "--quota"),
    gid: int = typer.Option(None, "--gid"),
):
    """Create a new account"""

    session = get_db_session()

    try:
        session.add(
            Account(
                username=username,
                status=ARG_TO_STATUS[status],
                quota=quota,
                gid=gid,
            )
        )
        session.commit()
        print(f"Successfully created account {username}.")
    except Exception as e:
        print(f"Could not create account {username}!")
        print(f"Details:\n{e}")
        exit(1)


@app.command()
def get(username: str):
    """Display all account information"""

    session = get_db_session()

    res = (
        session.query(Account)
        .filter(
            Account.username == username,
        )
        .first()
    )

    if not res:
        print(f"Account {username} not found!")
    else:
        print(json.dumps(res.to_dict()))


@app.command()
def update(
    username: str,
    status: str = typer.Option(None, "--status"),
    quota: int = typer.Option(None, "--quota"),
    gid: int = typer.Option(None, "--gid"),
):
    """Update an account with relevant attributes"""

    session = get_db_session()

    existing = session.query(Account).filter(Account.username == username).first()
    existing_dict = existing.to_dict()

    changes = {}

    if status is not None and existing.status != ARG_TO_STATUS[status]:
        changes[Account.status] = ARG_TO_STATUS[status]

    if quota is not None and existing.quota != quota:
        changes[Account.quota] = quota

    if gid is not None and existing.gid != gid:
        changes[Account.gid] = gid

    if not changes:
        print("No changes to be made, so not attempting update.")
        exit(0)

    res = (
        session.query(Account)
        .filter(
            Account.username == username,
        )
        .update(changes)
    )
    session.commit()

    if res:
        print(f"Account {username} updated successfully.")
        print("Details:")
        for k, v in changes.items():
            print(f"  {k.name} changed from {existing_dict[k.name]} to {v}")

    else:
        print(f"Account {username} could not be updated! See logs for more details.")
        exit(1)


@app.command()
def delete(username: str):
    """Remove an account and all associated data"""

    session = get_db_session()
    res = session.delete(Account(username=username))
    if res:
        print(f"Account {username} deleted successfully.")
    else:
        print(f"Account {username} could not be updated! See logs for more details.")
        exit(1)

# TODO: validate command
