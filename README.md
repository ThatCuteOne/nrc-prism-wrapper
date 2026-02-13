

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
| Flag                             | Variable             | description                                                                  | Default value           |
| -------------------------------- | -------------------- | ---------------------------------------------------------------------------- | ----------------------- |
| `-l` & `--launcher`              | LAUNCHER_TYPE        | Overrides the automatic launcher detection Options: prism \| modrinth        | None                    |
| `--modrinth-data-path`           | MODRINTH_DATA_PATH   | Path to the dir that contains app.db                                         | ../../                  |
| `--prism-data-path`              | PRISM_DATA_PATH      | path to the dir that contains accounts.json                                  | ../../..                |
| `-p` & `--norisk-pack`           | NORISK_PACK          | Norisk pack to use                                                           | norisk-prod             |
| `-m` & `--mc-version`            | None                 | Overrides the automatic minecraft version detection(intended for debugging)  | auto                    |
| `-n` & `--nrc-mod-path`          | NRC_MOD_PATH         | The path where the norisk client mods will be installed                      | ./mods/NoriskClientMods |
| `-nv` & `--no-hash-verification` | NO_HASH_VERIFICATION | Prevents crashes if the file hashes are mismatched (workaround for api bugs) | False                   |


### Todos
- look into python venv 
- run arg for disabling jar injection
- set dev enviroment via env variable
- log steaming into modrinth app(if possible)


#### Ideas
- profile sync and convertion between nrc and prism
