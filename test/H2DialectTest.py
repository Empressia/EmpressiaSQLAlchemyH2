import data.REGULAR;
import data.MSSQLServer;
import data.MySQL;
import data.Oracle;
import data.PostgreSQL;
import empressia_sqlalchemy_h2;
import empressia_sqlalchemy_h2.H2DialectException;
import inspect;
import json;
import os;
import sqlalchemy.orm;
import unittest;

class H2DialectTest(unittest.TestCase):
	"""
	H2Dialectのテストです。
	config.jsonに、
	JAVA_HOMEを指定すると、テスト時に環境変数に設定されます。
	H2Pathを指定すると、テスト時にそのパスが使用されます。
	H2HashにH2PathのファイルのSHA-256のハッシュ値（16進数文字列）を設定すると、H2Pathの先が存在しない場合にMavenからのダウンロードを試みます。
	"""

	_H2Path: str|None = None;

	def setUp(self):
		config: dict[str, str] = {};
		path: str|None;
		hash: str|None = None;
		if(os.path.exists("config.json")):
			with(open("config.json", "r", encoding="UTF-8") as f):
				config = json.load(f);
		if(config.get("JAVA_HOME") != None):
			os.environ["JAVA_HOME"] = config["JAVA_HOME"];
		if(config.get("H2Path") != None):
			self._H2Path = config["H2Path"];
		if(config.get("H2Hash") != None):
			hash = config["H2Hash"];
		path = self._H2Path;
		if((path != None) and (os.path.exists(path) == False) and (hash != None)):
			import pathlib;
			pathlib.Path(path).stem;
			(a, *vs) = pathlib.Path(path).stem.split("-", 1);
			if((a == "h2") and (len(vs) == 1)):
				v = vs[0];
				import urllib.request;
				URL = f"https://repo1.maven.org/maven2/com/h2database/{a}/{v}/{a}-{v}.jar";
				with(urllib.request.urlopen(URL) as r):
					fileBytes = r.read();
					import hashlib;
					hasher = hashlib.sha256();
					hasher.update(fileBytes);
					hashString = hasher.hexdigest();
				# hexdigestが小文字を返すようなのでそちらにそろえている（定義上には明記されていなかった）。
				if(hashString.lower() == hash.lower()):
					with(open(path, "wb") as f):
						f.write(fileBytes);
						f.close();
				else:
					raise empressia_sqlalchemy_h2.H2DialectException("H2のjarの検証に失敗しました。");
			else:
				raise empressia_sqlalchemy_h2.H2DialectException("H2のjarのファイル名の確認に失敗しました。");

	def test_シンプルに接続できてSQL操作できる(self):
		if(self._H2Path != None):
			os.environ["CLASSPATH"] = self._H2Path;
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name}"); # type: ignore[reportGeneralTypeIssues]
		with(sqlalchemy.orm.Session(engine) as s):
			q = sqlalchemy.text("CREATE TABLE \"User\" (ID INTEGER NOT NULL, NAME VARCHAR(256) NOT NULL, PRIMARY KEY (ID, NAME))");
			s.execute(q);
			q = sqlalchemy.text("INSERT INTO \"User\" VALUES (0, 'UserName')");
			s.execute(q);
			q = sqlalchemy.text("SELECT * FROM \"User\"");
			result = s.execute(q);
			rows = list(result);
			self.assertEqual(len(rows), 1);
			self.assertEqual(rows[0][0], 0);
			self.assertEqual(rows[0][1], "UserName");

	def test_メタデータからテーブルを作れる(self):
		jars = [self._H2Path] if (self._H2Path != None) else [];
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name}", echo=False, jars=jars); # type: ignore[reportGeneralTypeIssues]
		data.REGULAR.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.REGULAR.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.REGULAR.User = s.query(data.REGULAR.User).filter(data.REGULAR.User.ID == 0).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");

	def test_MSSQLServerでメタデータからテーブルを作れる(self):
		# limitが通る。TOPになる。
		mode = empressia_sqlalchemy_h2.CompatibilityMode.MSSQLServer;
		jars = [self._H2Path] if (self._H2Path != None) else [];
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name};MODE={mode.name}", echo=False, jars=jars); # type: ignore[reportGeneralTypeIssues]
		data.MSSQLServer.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.MSSQLServer.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.MSSQLServer.User = s.query(data.MSSQLServer.User).filter(data.MSSQLServer.User.ID == 0).limit(1).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");

	def test_MariaDBでメタデータからテーブルを作れる(self):
		# MySQLと同じ感じで使用できる。
		mode = empressia_sqlalchemy_h2.CompatibilityMode.MariaDB;
		jars = [self._H2Path] if (self._H2Path != None) else [];
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name};MODE={mode.name}", echo=False, jars=jars); # type: ignore[reportGeneralTypeIssues]
		data.MySQL.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.MySQL.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.MySQL.User = s.query(data.MySQL.User).filter(data.MySQL.User.ID == 0).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");

	def test_MySQLでメタデータからテーブルを作れる(self):
		# DATETIMEの桁数指定が使用できる。
		# 文字列の列は、長さ指定がないと落ちる。
		# ON DUPLICATE KEY UPDATEを構成できる。
		# Floatへのキャストを構成できる。
		# ESCAPE付きのLIKEを構成できる。
		mode = empressia_sqlalchemy_h2.CompatibilityMode.MySQL;
		jars = [self._H2Path] if (self._H2Path != None) else [];
		# create_engineよりあとにimportすると、create_engineがエラーになったりする（sqlalchemy 2.0.40）。
		# 他にも問題起きる。起きている。けど、とりあえず、動く。
		import sqlalchemy.sql.sqltypes;
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name};MODE={mode.name}", echo=False, jars=jars); # type: ignore[reportGeneralTypeIssues]
		data.MySQL.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.MySQL.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.MySQL.User = s.query(data.MySQL.User).filter(data.MySQL.User.ID == 0).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");
			import sqlalchemy.dialects.mysql;
			q = sqlalchemy.dialects.mysql.insert(data.MySQL.User).values(ID = 0, Name = "UserName");
			q = q.on_duplicate_key_update(
				Name = q.inserted.Name
			);
			s.execute(q);
			s.commit();
			v = s.query(sqlalchemy.cast(data.MySQL.User.ID, sqlalchemy.sql.sqltypes.Float)).with_for_update(of=data.MySQL.User).scalar();
			self.assertEqual(v, 0);
			u = s.query(data.MySQL.User).filter(data.MySQL.User.Name.like("UserName", escape="\\")).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");

	def test_Oracleでメタデータからテーブルを作れる(self):
		# 文字列の列に、長さを指定できる。
		# Unicodeを指定できる。
		mode = empressia_sqlalchemy_h2.CompatibilityMode.Oracle;
		jars = [self._H2Path] if (self._H2Path != None) else [];
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name};MODE={mode.name}", echo=False, jars=jars); # type: ignore[reportGeneralTypeIssues]
		data.Oracle.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.Oracle.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.Oracle.User = s.query(data.Oracle.User).filter(data.Oracle.User.ID == 0).limit(1).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");

	def test_PostgreSQLでメタデータからテーブルを作れる(self):
		# TIMESTAMP WITHOUT TIME ZONEの桁数指定が使用できる。
		# ESCAPE付きのLIKEを構成できる。
		# Indexを作って消せる。
		mode = empressia_sqlalchemy_h2.CompatibilityMode.PostgreSQL;
		jars = [self._H2Path] if (self._H2Path != None) else [];
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name};MODE={mode.name}", echo=False, jars=jars); # type: ignore[reportGeneralTypeIssues]
		data.PostgreSQL.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.PostgreSQL.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.PostgreSQL.User = s.query(data.PostgreSQL.User).filter(data.PostgreSQL.User.ID == 0).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");
			u = s.query(data.PostgreSQL.User).filter(data.PostgreSQL.User.Name.like("UserName", escape="\\")).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");
			i = sqlalchemy.Index("INDEX_User_UserName", data.PostgreSQL.User.Name);
			i.create(s.get_bind());
			i.drop(s.get_bind());
			s.commit();

	def test_DelegateDialectを指定して動作を差し替えられる(self):
		# 動くかわからないけど。
		mode = empressia_sqlalchemy_h2.CompatibilityMode.REGULAR;
		jars = [self._H2Path] if (self._H2Path != None) else [];
		import sqlalchemy.dialects.sqlite;
		engine = sqlalchemy.create_engine(f"h2:///mem:{inspect.currentframe().f_code.co_name};MODE={mode.name}", echo=False, jars=jars, DelegateDialect=sqlalchemy.dialects.sqlite.base.SQLiteDialect()); # type: ignore[reportGeneralTypeIssues]
		data.REGULAR.EntityBase.metadata.create_all(engine);
		with(sqlalchemy.orm.Session(engine) as s):
			u = data.REGULAR.User();
			u.ID = 0;
			u.Name = "UserName";
			s.add(u);
			s.commit();
			u: data.REGULAR.User = s.query(data.REGULAR.User).filter(data.REGULAR.User.ID == 0).scalar();
			self.assertEqual(u.ID, 0);
			self.assertEqual(u.Name, "UserName");
			v = s.query(sqlalchemy.cast(data.REGULAR.User.ID, sqlalchemy.dialects.sqlite.INTEGER)).scalar();
			self.assertEqual(v, 0);

	def test_DelegateAttributesを指定して存在しない属性を登録できる(self):
		original = empressia_sqlalchemy_h2.H2Dialect();
		registered = empressia_sqlalchemy_h2.H2Dialect(DelegateAttributes={ "test":True });
		with(self.assertRaises(AttributeError)):
			original.test;
		self.assertEqual(registered.test, True);

	def test_DelegateAttributesを指定して存在する属性を上書きできる(self):
		original = empressia_sqlalchemy_h2.H2Dialect();
		modified = empressia_sqlalchemy_h2.H2Dialect(DelegateAttributes={ "default_sequence_base":original.default_sequence_base-1 });
		self.assertNotEqual(original.default_sequence_base, modified.default_sequence_base);

	def test_DelegateAttributesを指定して存在するプロパティを差し替えられる(self):
		original = empressia_sqlalchemy_h2.H2Dialect();
		modified = empressia_sqlalchemy_h2.H2Dialect(DelegateAttributes={ "supports_identity_columns":False });
		self.assertNotEqual(original.supports_identity_columns, modified.supports_identity_columns);

	def test_URLが期待通りに解析される(self):
		normalCases = [
			{ "url":"h2:///mem:TestDB", "subname":"mem:TestDB" },
			{ "url":"h2+jaydebeapi:///mem:TestDB", "subname":"mem:TestDB" },
			{ "url":"h2:///mem:TestDB;MODE=MSSQLServer", "subname":"mem:TestDB;MODE=MSSQLServer" }
		];
		for normalCase in normalCases:
			subname = empressia_sqlalchemy_h2.H2Dialect.extractSubname(normalCase["url"]);
			self.assertEqual(subname, normalCase["subname"]);
		illegalCases = [ { "url":"" }, { "url":"h2://localhost/h2"} ];
		for illegalCase in illegalCases:
			with(self.assertRaises(empressia_sqlalchemy_h2.H2DialectException)):
				empressia_sqlalchemy_h2.H2Dialect.extractSubname(illegalCase["url"]);
