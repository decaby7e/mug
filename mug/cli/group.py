import typer

from ..connections import get_db_session
from ..models import Group

app = typer.Typer(name="group", help="Various utilities for working with groups")


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


@app.command()
def create(
    username: str,
    status: str = typer.Option("personal", "--status"),
    quota: int = typer.Option(0, "--quota"),
    group: str = typer.Option("", "--group"),
):
    """Create a new account"""

    session = get_db_session()


@app.command()
def get(username: str):
    """Display all account information"""

    session = get_db_session()

    print(
        session.query(Account)
        .filter(
            Account.username == username,
        )
        .first()
    )


@app.command()
def update(
    username: str,
    status: str = typer.Option("personal", "--status"),
    quota: int = typer.Option(0, "--quota"),
    group: str = typer.Option("", "--group"),
):
    """Update an account with relevant attributes"""
    ARG_TO_STATUS = {
        "disabled": "DISABLED",
        "personal": "USING_PERSONAL_QUOTA",
        "group": "USING_GROUP_QUOTA",
    }

    session = get_db_session()

    existing = session.query(Account).filter(Account.username == username).first()

    changes = {}

    if existing.status != status:
        changes["status"] = ARG_TO_STATUS[status]

    if existing.quota != quota:
        changes["quota"] = ARG_TO_STATUS[status]

    session.query(Account).filter(
        Account.username == username,
    ).update(**changes)


@app.command()
def delete(username: str):
    """Remove an account and all associated data"""

    session = get_db_session()
    session.delete(Account(username=username))
