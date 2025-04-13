import datetime;
import sqlalchemy.orm;
from .EntityBase import EntityBase;

class User(EntityBase):
	ID: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True, autoincrement=False, comment="ID");
	Name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(server_default="匿名");
	Memo: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(nullable=True);
	Roles: sqlalchemy.orm.Mapped[list[lambda:UserRole]] = sqlalchemy.orm.relationship( # type: ignore[reportGeneralTypeIssues]
		cascade="all, delete",
		order_by=(lambda:[UserRole.ID, UserRole.Name])
	);
	__tablename__ = "User";

class UserRole(EntityBase):
	ID: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True);
	Name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True);
	ExpriredAt: sqlalchemy.orm.Mapped[datetime.datetime];
	__table_args__ = (
		sqlalchemy.ForeignKeyConstraint(
			[ID],
			[User.ID]
		),
	);
	__tablename__ = "UserRole";
