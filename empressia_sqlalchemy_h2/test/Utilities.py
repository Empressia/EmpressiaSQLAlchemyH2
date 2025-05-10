import urllib.request;
import os;
import pathlib;
from ..H2DialectException import H2DialectException;

class Utilities:
	"""
	テスト用のユーティリティです。
	H2 Databaseをテストに使用することが多いと思うので、便利そうな関数を提供します。
	"""

	@staticmethod
	def downloadH2Jar(path: str, hash: str):
		"""
		バージョンを指定して、H2 Databaseのjarをダウンロードします。
		原則、Mavenからダウンロードする想定です。
		すでに存在する場合は、ダウンロードしません。

		path……保存先のH2のjarのパス。ファイル名はh2-<version>.jarとなっている想定です。
		hash……H2のjarのSHA-256での16進数ハッシュ値です。ダウンロードしたときにチェックされます。
		"""
		if(os.path.exists(path) == False):
			pathlib.Path(path).stem;
			(a, *vs) = pathlib.Path(path).stem.split("-", 1);
			if((a == "h2") and (len(vs) == 1)):
				v = vs[0];
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
					raise H2DialectException("H2のjarの検証に失敗しました。");
			else:
				raise H2DialectException("H2のjarのファイル名の確認に失敗しました。");
