

> [!WARNING]
> **Attention:** There may be security issues since i dont know anything about security, so i cant guarantee any.

# Features
- Run [Norisk Client](https://norisk.gg/) trough prism launcher or the modrinth app(linux only)
- Full Resourcepack support(modifiy any noriskclient asset you want via a resourcepack)

## Requirements:
- python 3.x+
- [Required Python packages](https://github.com/ThatCuteOne/nrc-prism-wrapper/blob/master/req.txt)(should be installed automatically)

On some systems(debain based for example) you may need to install the dependencies manually, just look at the [req.txt](https://github.com/ThatCuteOne/nrc-prism-wrapper/blob/master/req.txt) or the [get_dependencies.py](https://github.com/ThatCuteOne/nrc-prism-wrapper/blob/master/src/tasks/get_dependencies.py)


# Usage
1. Download the nrc-wrapper.pyz from the [releases page](https://github.com/ThatCuteOne/nrc-prism-wrapper/releases)
2. Go into Prism(multimc may also work) edit an instance, go to **Settings>Custom Commands**
3. In "Wrapper command" Enter:
```
python path/to/nrc-wrapper.pyz
```
4. Start your instance
everything else should happen automaticaly


_NOTE: Currently only the fabric versions are supported(1.21+)_

You may also want to checkout technicfans wrapper thats written in go(lang) [here](https://github.com/technicfan/nrc-wrapper-go)

# Settings
| Flag                   | Variable           | description                                                           | Default value |
| ---------------------- | ------------------ | --------------------------------------------------------------------- | ------------- |
| `-l` & `--launcher`    | LAUNCHER_TYPE      | Overrides the automatic launcher detection Options: prism \| modrinth | None          |
| `--modrinth-data-path` | MODRINTH_DATA_PATH | Path to the dir that contains app.db                                  | ../../        |
| `--prism-data-path`    | PRISM_DATA_PATH    | path to the dir that contains accounts.json                           | ../../..      |
| `-p` & `--norisk-pack` | NORISK_PACK        | Norisk pack to use                                                    | norisk-prod   |


### Todos
- delete old mod files when swiching modpack or gameversion
- settings via enviroment variables
- look into python venv 
- run arg for disabling jar injection
- set dev enviroment via env variable
- log steaming into modrinth app(if possible)
- verfiy downloads by hash matching with maven repo(http://maven.norisk.gg/repository/norisk-production/gg/norisk/nrc-ui/1.0.78+fabric.1.21.7/nrc-ui-1.0.78+fabric.1.21.7.jar.md5/sha1/sha257/sha512) and modrinth


#### Ideas
- profile sync and convertion between nrc and prism
