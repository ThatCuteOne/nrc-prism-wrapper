

> [!WARNING]
> **Attention:** There may be security issues since i dont know anything about security, so i cant guarantee any.

# Features
- Run [Norisk Client](https://norisk.gg/) trough prism launcher or the modrinth app(linux only)
- remove norisk client watermark
- replace any asset via an assetpack(Modules, Emotes,Cosmetics)

## Requirements:
- python 3.x+
- [Required Python packages](https://github.com/ThatCuteOne/nrc-prism-wrapper/blob/master/req.txt)(should be installed automatically)

On some systems(debain based for example) you may need to install the dependencies manually, just look at the [req.txt](https://github.com/ThatCuteOne/nrc-prism-wrapper/blob/master/req.txt) or the [get_dependencies.py](https://github.com/ThatCuteOne/nrc-prism-wrapper/blob/master/src/tasks/get_dependencies.py)


# Usage
1. You need to have logged into the default NRC(Norisk Client) Launcher at least once.
2. Download the nrc-wrapper.pyz from the [releases page](https://github.com/ThatCuteOne/nrc-prism-wrapper/releases)
2. Go into Prism(multimc may also work) edit an instance, go to **Settings>Custom Commands**
3. In "Wrapper command" Enter:
```
python path/to/nrc-wrapper.pyz
```
4. Start your instance
everything else should happen automaticaly


_NOTE: Currently only the fabric versions are supported(1.21+)_


## Assetpacks
> Asset packs are bascally resource packs but they are only loaded at gamestart and from the "nrc_asset_overrides" directory(in your instance)
> they need a pack.mcmeta file(can be empty), another caviat is that there currently is no deterministic load order



### Todos
- log steaming into modrinth app(if possible)
- set modloader version
- handle assets other then prod
- verfiy downloads by hash matching with maven repo(http://maven.norisk.gg/repository/norisk-production/gg/norisk/nrc-ui/1.0.78+fabric.1.21.7/nrc-ui-1.0.78+fabric.1.21.7.jar.md5/sha1/sha257/sha512) and modrinth
- force newest setting(force install newest versions from maven repo or modrinth)
- make asset packs reloadable(idk how)



#### Ideas
- profile sync and convertion between nrc and prism
