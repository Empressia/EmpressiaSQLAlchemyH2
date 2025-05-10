# Empressia SQLAlchemy H2

## 概要

Empressia製のSQLAlchemy用のDialectです。  
H2 DatabaseへのJayDeBeApiを使用したJDBC接続をサポートします。  
接続するための最低限の実装と、基本的な委譲で行えるマッピングしかしていません。  

## 使い方

sqlalchemy.create_engineを呼ぶ前に、empressia_sqlalchemy_h2をimportしておいてください。  
SQLAlchemyへDialectを登録します。  

```python
import empressia_sqlalchemy_h2;
```

JayDeBeApiを使用しているため、  
環境変数JAVA_HOMEに、JDKへのパスを指定しておく必要があります。  
例えば、pythonで設定するには以下のようにします。  

```python
os.environ["JAVA_HOME"] = r"/path/to/JDK/";
```

H2のjarへのパスは、環境変数CLASSPATHに設定するか、  
sqlalchemy.create_engineにjars引数として文字列の配列で渡してください。  

```python
os.environ["CLASSPATH"] = r"/path/to/h2-<version>.jar";
```

```python
sqlalchemy.create_engine("<URL>", jars=[r"/path/to/h2-<version>.jar"]);
```

URLは、以下の形式をサポートしています。  

> h2:///<database>  
> h2+jaydebeapi:///<database>  

databaseには、JDBCのsubnameを指定します。  

例えば、次のようなJDBCの接続文字列について考えます。  

> jdbc:h2:mem:TestDB  

この場合は、以下がsubnameとなります。  

> mem:TestDB  

sqlalchemy.create_engineに渡すURLは、次のようになります。  

> h2:///mem:TestDB  

subnameにMODEを指定することで、勝手に、Dialectの動作を切り替えます。  
MSSQLServer、MariaDB、MySQL、Oracle、PostgreSQLのモードであれば、これだけで十分だと思います。  

> h2:///mem:TestDB;MODE=MSSQLServer  

さらに、Dialectの振る舞いを差し替えたい場合は、  
sqlalchemy.create_engineを呼ぶときに、DelegateDialectを指定するか、DelegateAttributesを指定してください。  
妥当と思う範囲で振る舞いを委譲します。  

Dialectを用意してある場合は、DelegateDialectを指定してください。  
Dialectを用意してない場合や、DelegateDialectだけでは問題が起きる場合は、DelegateAttributesを指定してください。  
DelegateAttributesを優先的に使用します。  

## テスト用のユーティリティ

テスト用に、ユーティリティを用意しています。  
H2 Databaseのjarファイルをダウンロードすることができます。  

```
empressia_sqlalchemy_h2.test.Utilities.downloadH2Jar("h2-<version>.jar", "<SHA-256 HEX文字列>");
```

## その他

このプロジェクトをテストするときは、config.jsonを用意します。  
パスなどが通っていればいりません。  

```json
{
	"JAVA_HOME" : "/path/to/JDK/",
	"H2Path" : "h2-<version>.jar",
	"H2Hash" : "h2-<version>.jarのSHA-256の16進数表現"
}
```
