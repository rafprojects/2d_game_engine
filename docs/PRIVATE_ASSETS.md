# Private assets

These files stay in this private repo for local development. A public release
omits them. The sprite trees, both spritesheets, and the NSF are extracts from
the commercial NES game The Guardian Legend. The OPL3 soundfont is bundled
beside that audio path and leaves with the same release cut.

- `assets/sprites/ship/`
- `assets/sprites/enemies/`
- `assets/sprites/walking/`
- `assets/sprites/transform/`
- `assets/sprites/ending/`
- `assets/sprites/weapons/`
- `assets/spritesheets/bosses.png`
- `assets/spritesheets/enemies.png`
- `assets/music/Guardian_Legend.nsf`
- `assets/soundfonts/OPL-3_FM_128M.sf2`

`assets/player.png` and `assets/player_sheet.png` are generic test sprites and
are not on this list.

`tgl_demo` currently resolves the ship, asteroid, and bullet art through the
engine asset tree. Packing a cartridge for anyone else means replacing those
files, not copying this list into the archive.
