import enum;

class CompatibilityMode(enum.Enum):
	"""
	H2 Databaseの Compatibility Modeです。
	"""
	REGULAR = enum.auto();
	STRICT = enum.auto();
	LEGACY = enum.auto();
	DB2 = enum.auto();
	Derby = enum.auto();
	HSQLDB = enum.auto();
	MSSQLServer = enum.auto();
	MariaDB = enum.auto();
	MySQL = enum.auto();
	Oracle = enum.auto();
	PostgreSQL = enum.auto();
