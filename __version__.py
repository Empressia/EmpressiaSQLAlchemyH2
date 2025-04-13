import hatchling.metadata.plugin.interface;
import pygit2.repository;
import typing;

class VersionMetadataHook(hatchling.metadata.plugin.interface.MetadataHookInterface):
	"""
	Hatch用に、バージョンをGitから提供します。
	現在のHEADのタグ名をバージョンとします。
	無い場合はさかのぼって探します。
	探した場合は、4番目をインクリメントし、devを付与します。
	見つからない場合は、0.0.0.1.devとなります。
	タグから、バージョンにそのまま変換できない場合はtoVersionを書き換えます。
	"""

	@staticmethod
	def toVersion(tag: pygit2.Reference):
		""" タグからバージョンの文字列に変換します。 """
		return tag.shorthand;

	def update(self, metadata: dict[typing.Any, typing.Any]):
		versionString: str|None = None;

		CommitIDTags: dict[pygit2.Oid, pygit2.Reference] = {};

		r = pygit2.repository.Repository("");
		for refString in r.references:
			if(refString.startswith("refs/tags/")):
				tag = r.lookup_reference(refString);
				CommitIDTags[tag.peel(pygit2.Commit).id] = tag; # type: ignore[reportUnknownMemberType]

		if(r.head_is_unborn == False):
			HeadCommitID = r.head.peel(pygit2.Commit).id; # type: ignore[reportUnknownMemberType]
			for commit in r.walk(r.head.target, pygit2.enums.SortMode.TOPOLOGICAL|pygit2.enums.SortMode.REVERSE):
				tag = CommitIDTags.get(commit.id);
				if(tag != None):
					if(commit.id == HeadCommitID):
						versionString = VersionMetadataHook.toVersion(tag);
					else:
						versionParts = VersionMetadataHook.toVersion(tag).split(".");
						if(len(versionParts) > 4):
							continue;
						else:
							while(len(versionParts) < 4):
								versionParts.append("0");
						try:
							lastPartAsInt = int(versionParts[-1]);
						except(ValueError):
							continue;
						versionParts[-1] = str(lastPartAsInt + 1);
						versionString = ".".join(versionParts) + ".dev";
					break;

		versionString = versionString if (versionString != None) else "0.0.0.1.dev";
		metadata["version"] = versionString;
