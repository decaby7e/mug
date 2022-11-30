from datetime import datetime

from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy_serializer import SerializerMixin

#
#  Constants
#

ALLOWED_STATUS = ["DISABLED", "USING_PERSONAL_QUOTA", "USING_GROUP_QUOTA"]

#
#  Models
#

Base = declarative_base()


class Account(Base, SerializerMixin):
    """Basic account with default quota, pages printed, and a group"""

    __tablename__ = "account"
    username = Column(String(64), nullable=False, primary_key=True)
    gid = Column(Integer, nullable=True)
    status = Column(Enum(*ALLOWED_STATUS, name="allowed_status"), nullable=False)
    quota = Column(Integer)
    pages_printed = Column(Integer, default=0, nullable=False)
    date_added = Column(DateTime(), default=datetime.now())
    date_modified = Column(DateTime())


class Group(Base, SerializerMixin):
    """Basic quota group"""

    __tablename__ = "group"
    gid = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(64), nullable=False)
    page_count = Column(Integer)
