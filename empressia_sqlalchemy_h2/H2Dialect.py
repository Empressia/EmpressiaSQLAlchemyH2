import jaydebeapi; # type: ignore[reportMissingTypeStubs]
import sqlalchemy.engine.default;
import typing;
from .CompatibilityMode import *;
from .H2DialectException import *;

class H2Dialect(sqlalchemy.engine.default.DefaultDialect):
	"""
	Empressia製のSQLAlchemy用のDialectです。
	H2 DatabaseへのJayDeBeApiを使用したJDBC接続をサポートします。
	接続するための最低限の実装と、基本的な委譲で行えるマッピングしかしていません。

	sqlalchemy.create_engineを呼ぶ前に、empressia_sqlalchemy_h2をimportしておいてください。
	SQLAlchemyへDialectを登録します。
	import empressia_sqlalchemy_h2;

	JayDeBeApiを使用しているため、
	環境変数JAVA_HOMEに、JDKへのパスを指定しておく必要があります。
	例えば、pythonで設定するには以下のようにします。
	os.environ["JAVA_HOME"] = r"/path/to/JDK/";

	H2のjarへのパスは、環境変数CLASSPATHに設定するか、
	sqlalchemy.create_engineにjars引数として文字列の配列で渡してください。
	os.environ["CLASSPATH"] = r"/path/to/h2-<version>.jar";
	sqlalchemy.create_engine("<URL>", jars=[r"/path/to/h2-<version>.jar"]);

	URLは、以下の形式をサポートしています。
	h2:///<database>
	h2+jaydebeapi:///<database>
	databaseには、JDBCのsubnameを指定します。

	例えば、次のようなJDBCの接続文字列について考えます。
	jdbc:h2:mem:TestDB
	この場合は、以下がsubnameとなります。
	mem:TestDB
	sqlalchemy.create_engineに渡すURLは、次のようになります。
	h2:///mem:TestDB

	subnameにMODEを指定することで、勝手に、Dialectの動作を切り替えます。
	MSSQLServer、MariaDB、MySQL、Oracle、PostgreSQLのモードであれば、これだけで十分だと思います。
	h2:///mem:TestDB;MODE=MSSQLServer  

	さらに、Dialectの振る舞いを差し替えたい場合は、
	sqlalchemy.create_engineを呼ぶときに、DelegateDialectを指定するか、DelegateAttributesを指定してください。
	妥当と思う範囲で振る舞いを委譲します。

	Dialectを用意してある場合は、DelegateDialectを指定してください。
	Dialectを用意してない場合や、DelegateDialectだけでは問題が起きる場合は、DelegateAttributesを指定してください。
	DelegateAttributesを優先的に使用します。
	"""

	name = "h2";

	driver = jaydebeapi.__name__;

	default_schema_name = "PUBLIC";

	supports_statement_cache = True;
	""" 標準のキャッシュに従います。Dialectクラスで明示的に設定するように書かれているから設定しています。 """

	_jars: list[str] = [];
	""" H2のjarを指定するために用意しています。 """

	_CompatibilityMode: CompatibilityMode|None = None;

	# region: 委譲するための領域
	_DelegateDialect: sqlalchemy.engine.interfaces.Dialect|None = None;
	""" CompatibilityModeの指定だけでは解決できないDialect情報を指定します。 """

	_DelegateAttributes: dict[str, object]|None = None;
	""" CompatibilityModeやDelegateDialectの指定だけでは解決できないDialect情報を指定します。 """
	# endregion: 委譲するための領域

	R = typing.TypeVar("R");
	def _getFromDelegate(self, name: str, defaultValueFunction: typing.Callable[[], R]):
		if((self._DelegateAttributes != None) and (name in self._DelegateAttributes)):
			return self._DelegateAttributes[name];
		elif(self._DelegateDialect != None):
			return getattr(self._DelegateDialect, name);
		else:
			return defaultValueFunction();
	def __getattr__(self, name: str):
		""" 任意の要求に応えるためのもの。 """
		return self._getFromDelegate(name, lambda: (_ for _ in ()).throw(
			AttributeError(f"『{self.__class__.__name__}』に『{name}』はありません。")
		));

	# region: 特定のDialect専用領域
	# TypeComilerはDialectインスタンスを差し込めるんだけど、
	# DDLCompilerはクラスしか指定できなくて、このDialectが強制的に使われてしまうから、
	# 必要な情報を実装しなくちゃいけない。
	@property
	def legacy_schema_aliasing(self):
		""" MSSQLServerが要求している。 """
		return self._getFromDelegate("legacy_schema_aliasing", lambda: False);
	@property
	def _supports_offset_fetch(self):
		""" MSSQLServerとOracleが要求している。新しいのはサポートしているみたいだからTrueを返している。 """
		return self._getFromDelegate("_supports_offset_fetch", lambda: True);
	@property
	def is_mariadb(self):
		""" MySQLとMariaDBが要求している。 """
		return self._getFromDelegate("is_mariadb", lambda: (self._CompatibilityMode == CompatibilityMode.MariaDB));
	@property
	def _backslash_escapes(self):
		""" MySQLとMariaDBとPostgreSQLが要求している。Trueが初期値みたいなんだけど、LIKEのESCAPEに『\\』を指定するとエラーになるから、初期値はFalsesにしている。 """
		return self._getFromDelegate("_backslash_escapes", lambda: False);
	@property
	def _support_default_function(self):
		""" MySQLとMariaDBが要求している。新しいのはサポートしているみたいだからTrueを返している。 """
		return self._getFromDelegate("_support_default_function", lambda: True);
	@property
	def supports_for_update_of(self):
		""" MySQLが要求している。MySQLの機能であって、MariaDBはサポートしていないみたい。新しいのはサポートしているみたいだから、MySQLではTrueを返している。 """
		return self._getFromDelegate("supports_for_update_of", lambda: (self._CompatibilityMode == CompatibilityMode.MySQL));
	@property
	def supports_sequences(self):
		""" MySQLが要求している。MySQLにはこの機能がなくて、MariaDBは新しいのでサポートしている。他のはサポートしているみたいだから、MySQL以外ではTrueを返している。 """
		# 明らかに、他と同じ構成で、差し替え可能だから、カバレッジ外とする。
		return self._getFromDelegate("supports_sequences", lambda: (self._CompatibilityMode != CompatibilityMode.MySQL)); # pragma: no cover
	@property
	def _support_float_cast(self):
		""" MySQLとMariaDBが要求している。新しいのはサポートしているみたいだからTrueを返している。 """
		return self._getFromDelegate("_support_float_cast", lambda: True);
	@property
	def _requires_alias_for_on_duplicate_key(self):
		""" MySQLとMariaDBが要求している。H2 Databaseは『ON DUPLICATE KEY UPDATE』自体を積極的にサポートしてないっぽいからFalseを返している。 """
		# https://github.com/h2database/h2database/issues/3043
		return self._getFromDelegate("_requires_alias_for_on_duplicate_key", lambda: False);
	@property
	def use_ansi(self):
		""" Oracleが要求している。Version 8i以外の想定で値を返している。 """
		return self._getFromDelegate("use_ansi", lambda: True);
	@property
	def _supports_char_length(self):
		""" Oracleが要求している。新しいのはサポートしているみたいだからTrueを返している。 """
		return self._getFromDelegate("_supports_char_length", lambda: True);
	@property
	def _use_nchar_for_unicode(self):
		""" Oracleが要求している。 """
		return self._getFromDelegate("_use_nchar_for_unicode", lambda: False);
	@property
	def supports_smallserial(self):
		""" PostgreSQLが要求している。Version 9.2以上の想定で値を返している。 """
		# 明らかに、他と同じ構成で、差し替え可能だから、カバレッジ外とする。
		return self._getFromDelegate("supports_smallserial", lambda: True); # pragma: no cover
	@property
	def _supports_create_index_concurrently(self):
		""" PostgreSQLが要求している。 """
		return self._getFromDelegate("_supports_create_index_concurrently", lambda: True);
	@property
	def _supports_drop_index_concurrently(self):
		""" PostgreSQLが要求している。Version 9.2以上の想定で値を返している。 """
		return self._getFromDelegate("_supports_drop_index_concurrently", lambda: True);
	@property
	def supports_identity_columns(self):
		""" 全般的に使われる。MySQL、MariaDBではサポートされていないけど、H2だと使おうと思えば使えるみたいだからTrueにしておく。 """
		return self._getFromDelegate("supports_identity_columns", lambda: True);
	@property
	def supports_native_enum(self):
		""" 全般的に使われる。MySQLとMariaDBとPostgreSQLがサポートしているみたい。H2だとサポートはしていないからFalseにしておく。 """
		# 明らかに、他と同じ構成で、差し替え可能だから、カバレッジ外とする。
		return self._getFromDelegate("supports_native_enum", lambda: False); # pragma: no cover
	# MSSQLServer:
	# deprecate_large_types 通らないからいらないと思っている。
	# server_version_info 通らないからいらないと思っている。
	# Oracle:
	# optimize_limits 通らないからいらないと思っている。
	# endregion: 特定のDialect専用領域

	def __init__(
			self,
			jars: list[str] = [],
			DelegateDialect: sqlalchemy.engine.interfaces.Dialect|None= None,
			DelegateAttributes: dict[str, object]|None = None,
			**kwargs: typing.Any):
		super().__init__(**kwargs);
		self._jars = jars;
		self._DelegateDialect = DelegateDialect;
		self._DelegateAttributes = DelegateAttributes;
		if(DelegateAttributes != None):
			for key in DelegateAttributes.keys():
				if(hasattr(self.__class__, key)):
					a = getattr(self.__class__, key);
					if(isinstance(a, property) and (a.fset == None)):
						# setterのないPropertyは設定できません。
						# 原則、このクラスのプロパティは、DelegateAttributeを参照しています。
						pass;
					else:
						setattr(self, key, DelegateAttributes[key]);

	@staticmethod
	def extractSubname(url: str):
		# SQLAlchemyでの定義は以下の感じです。
		# dialect+driver://username:password@host:port/database
		# このDialectでは以下をサポートします。
		# h2+jaydebeapi:///database
		# databaseはJDBCのsubnameに相当すると解釈します。
		# h2+jaydebeapi:///subname
		# h2ではsubnameをurl;setting=value[;setting=value]のような形式としています。
		START_WITHOUT_DRIVER = "h2://";
		START_WITH_DRIVER = "h2+jaydebeapi://";
		URL_WITHOUT_DATABASE_WITHOUT_DRIVER = START_WITHOUT_DRIVER + "/";
		URL_WITHOUT_DATABASE_WITH_DRIVER = START_WITH_DRIVER + "/";
		if(url.startswith(URL_WITHOUT_DATABASE_WITHOUT_DRIVER)):
			subname = url[len(URL_WITHOUT_DATABASE_WITHOUT_DRIVER):];
		elif(url.startswith(URL_WITHOUT_DATABASE_WITH_DRIVER)):
			subname = url[len(URL_WITHOUT_DATABASE_WITH_DRIVER):];
		else:
			if((url.startswith(START_WITHOUT_DRIVER) or url.startswith(START_WITH_DRIVER)) == False):
				raise H2DialectException(f"このDialectでは、url[{url}]は『dialect+driver://』として、『{START_WITHOUT_DRIVER}』、または、『{START_WITH_DRIVER}』で始まっている必要があります。");
			if((url.startswith(URL_WITHOUT_DATABASE_WITHOUT_DRIVER) or url.startswith(URL_WITHOUT_DATABASE_WITH_DRIVER)) == False):
				raise H2DialectException(f"このDialectでは、username:password@host:portは省略する必要があります。必要であれば、database部分に指定するJDBCのsubname総統の箇所に指定してください。");
			else:
				raise H2DialectException(f"この分岐は通りません。"); # pragma: no cover
		return subname;

	def create_connect_args(self, url: sqlalchemy.engine.URL):
		s: str = str(url);
		subname = H2Dialect.extractSubname(s);
		JDBCURL = "jdbc:h2:" + subname;
		(_, *settings) = JDBCURL.split(";");
		d = dict(s.split("=") for s in settings);
		self._CompatibilityMode = CompatibilityMode[d.get("MODE", CompatibilityMode.REGULAR.name)];
		if(self._DelegateDialect != None):
			self.ddl_compiler = self._DelegateDialect.ddl_compiler;
			self.statement_compiler = self._DelegateDialect.statement_compiler;
			# クラス変数だから、設定してもダメ。
			# self.type_compiler_cls = self._DelegateDialect.type_compiler_cls;
			self.type_compiler_instance = self._DelegateDialect.type_compiler_instance;
			self.preparer = self._DelegateDialect.preparer;
		else:
			match(self._CompatibilityMode):
				case CompatibilityMode.MSSQLServer:
					import sqlalchemy.dialects.mssql;
					self.ddl_compiler = sqlalchemy.dialects.mssql.base.MSDDLCompiler;
					# MSSQLStrictCompilerは使っていない。
					self.statement_compiler = sqlalchemy.dialects.mssql.base.MSSQLCompiler;
					# クラス変数だから、設定してもダメ。
					# self.type_compiler_cls = sqlalchemy.dialects.mssql.base.MSTypeCompiler;
					self.type_compiler_instance = sqlalchemy.dialects.mssql.base.MSTypeCompiler(self);
					# MSIdentifierPreparer_pymssqlは使っていない。
					self.preparer = sqlalchemy.dialects.mssql.base.MSIdentifierPreparer;
				case CompatibilityMode.MariaDB:
					import sqlalchemy.dialects.mysql;
					self.ddl_compiler = sqlalchemy.dialects.mysql.base.MySQLDDLCompiler;
					# MySQLCompiler_mariadbconnectorは使っていない。
					self.statement_compiler = sqlalchemy.dialects.mysql.base.MySQLCompiler;
					# クラス変数だから、設定してもダメ。
					# self.type_compiler_cls = sqlalchemy.dialects.mysql.mariadb.MariaDBTypeCompiler;
					self.type_compiler_instance = sqlalchemy.dialects.mysql.mariadb.MariaDBTypeCompiler(self);
					# MariaDBDialect_mysqlconnectorは使っていない。
					self.preparer = sqlalchemy.dialects.mysql.base.MariaDBIdentifierPreparer;
				case CompatibilityMode.MySQL:
					import sqlalchemy.dialects.mysql;
					self.ddl_compiler = sqlalchemy.dialects.mysql.base.MySQLDDLCompiler;
					# MySQLCompiler_mysqlconnectorは使っていない。
					# MySQLCompiler_mysqldbは使っていない。
					self.statement_compiler = sqlalchemy.dialects.mysql.base.MySQLCompiler;
					# クラス変数だから、設定してもダメ。
					# self.type_compiler_cls = sqlalchemy.dialects.mysql.base.MySQLTypeCompiler;
					self.type_compiler_instance = sqlalchemy.dialects.mysql.base.MySQLTypeCompiler(self);
					# MySQLIdentifierPreparer_mysqlconnectorは使っていない。
					self.preparer = sqlalchemy.dialects.mysql.base.MySQLIdentifierPreparer;
				case CompatibilityMode.Oracle:
					import sqlalchemy.dialects.oracle;
					self.ddl_compiler = sqlalchemy.dialects.oracle.base.OracleDDLCompiler;
					# OracleCompiler_cx_oracleは使っていない。
					self.statement_compiler = sqlalchemy.dialects.oracle.base.OracleCompiler;
					# クラス変数だから、設定してもダメ。
					# self.type_compiler_cls = sqlalchemy.dialects.oracle.base.OracleTypeCompiler;
					self.type_compiler_instance = sqlalchemy.dialects.oracle.base.OracleTypeCompiler(self);
					self.preparer = sqlalchemy.dialects.oracle.base.OracleIdentifierPreparer;
				case CompatibilityMode.PostgreSQL:
					import sqlalchemy.dialects.postgresql;
					self.ddl_compiler = sqlalchemy.dialects.postgresql.base.PGDDLCompiler;
					# PGCompiler_asyncpgは使っていない。
					# PGCompiler_pg8000は使っていない。
					self.statement_compiler = sqlalchemy.dialects.postgresql.base.PGCompiler;
					# クラス変数だから、設定してもダメ。
					# self.type_compiler_cls = sqlalchemy.dialects.postgresql.base.PGTypeCompiler;
					self.type_compiler_instance = sqlalchemy.dialects.postgresql.base.PGTypeCompiler(self);
					# PGIdentifierPreparer_asyncpgは使っていない。
					# PGIdentifierPreparer_pg8000は使っていない。
					# PGIdentifierPreparer_psycopgは使っていない。
					# PGIdentifierPreparer_psycopg2は使っていない。
					self.preparer = sqlalchemy.dialects.postgresql.base.PGIdentifierPreparer;
				case CompatibilityMode.REGULAR | _:
					import sqlalchemy.sql;
					self.ddl_compiler = sqlalchemy.sql.compiler.DDLCompiler;
					self.statement_compiler = sqlalchemy.sql.compiler.SQLCompiler;
					# クラス変数だから、設定してもダメ。
					# self.type_compiler_cls = sqlalchemy.sql.compiler.GenericTypeCompiler;
					self.type_compiler_instance = sqlalchemy.sql.compiler.GenericTypeCompiler(self);
					self.preparer = sqlalchemy.sql.compiler.IdentifierPreparer;

		kwargs: dict[str, object] = {
			"jclassname": "org.h2.Driver",
			"url": JDBCURL,
			"driver_args": [],
			"jars": self._jars,
			"libs": []
		};
		return ((), kwargs);

	@classmethod
	def import_dbapi(cls):
		return jaydebeapi;

	def has_table(self, connection: sqlalchemy.engine.base.Connection, table_name: str, schema: str|None = None, **kw: dict[str,object]):
		query = sqlalchemy.text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table_name").bindparams(
			schema=schema if(schema != None) else self.default_schema_name, table_name=table_name
		);
		count: int|None = connection.execute(query).scalar();
		has_table = ((count != None) and (count > 0));
		return has_table;

# 検出されるようにモジュールに宣言しておく。
dialect=H2Dialect;
