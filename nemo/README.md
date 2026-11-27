# Nemo Weapon Stat Tuner

Tunes weapon stats (ergonomics, recoil, spread, damage, projectile velocity) for a
set of primary and support weapons, armory throwables (grenades, mines, the shield,
the throwing knife), stratagems (orbital, eagle, defensive, and the
backpacks), explosion damage, and stratagem boosters. The tuning ships as
eighteen HellForge **stats mods** (`nemo-stats-<group>`),
each a
declarative `hellforge-stats.json` HellForge applies at data load, per player, with
its own guarded validation. There is no in-game Lua addon, no FFI, and no patch
loop — the stats files are the mods' only gameplay artifacts.

## Structure

- `src/<group>.yaml` — the author's source of truth, one file per mod (the
  filename stem is the group name; the mod id is `nemo-stats-<group>`). The
  eighteen files: `weapons-ar`, `weapons-dmr`, `weapons-shotgun`, `weapons-smg`,
  `weapons-laser`, `weapons-plasma`, `weapons-special`, `weapons-pistols`,
  `throwables`, `stratagems-backpacks`, `stratagems-defensive`,
  `stratagems-orbital`, `stratagems-eagle`, `weapons-mg`, `weapons-cannons`,
  `weapons-rocket`, `weapons-gl`, `boosters`. Each file is
  shaped like the stats file (category → target → field → value, field names as
  in the HellForge schema). Sections: `weapons`, `throwables`, `stratagems`,
  `backpacks`, `explosions`, `boosters`, and an optional `raw` (verbatim write
  pass-through; the scope swaps). Each file also carries a required top-level
  `description:` key: a plain string — a single line, or a lead line followed by
  a blank line and prose (the manifest's description lead; the build appends a
  blank line and a bullet list of the emitted top-level targets, a section-name
  bullet only when
  the mod carries more than one non-empty section, and nested section targets are
  excluded; a target carrying a `notes:` key has its note follow its bullet as an
  indented plain-text continuation, one line per note line, and a nested target's
  note is excluded with the target; the validator fails the build if the key is
  missing, empty, or a multi-line value that is not a lead line, a blank line,
  and prose). A value is a plain number, a plain boolean, or
  a plain string (a status-reference field such as `damage.status_1_type` takes
  a semantic status id like `fire`; `stratagem.max_uses` takes a number or `-1`
  for unlimited). The `# stock N` trailing notes are machine-maintained by the
  build (one aligned note column across the file set). A YAML file in `src/`
  whose stem is not a known group name fails the build.

  A target may also carry two reserved keys that never reach the stats file:
  `notes:` (a block-scalar string with the weapon's balance rationale, surfaced
  in the manifest description as an indented continuation under the target's
  bullet) and `raw:` (that weapon's raw write entries). A target may also nest a section
  under it — a key named after one of the file's sections (`weapons`,
  `throwables`, `stratagems`, `backpacks`, `explosions`, `boosters`) holds that
  section's targets under the logical weapon (the G-7 Pineapple's two
  `explosions` rows sit under `throwables: G-7 Pineapple: explosions:`; a
  weapon's underbarrel sits under its host's own `weapons:` key — a nested
  section key may equal the parent's own section; the MG-43 / M-105 scope swaps
  sit under their weapons' `raw:`). The build
  flattens the source shape to the flat section/target/field view before
  validating, generating, annotating, and tabling, so a nested config and an
  equivalent flat config emit byte-identical stats files.
- `scripts/` — the offline tooling (PEP 723, run via `uv`): `flatten.py` (the
  shared source-shape flattener: strips `notes:`, splices nested section targets
  and nested `raw:` entries into the flat section/target/field view the other
  tools consume), `validate_stats.py` (the validation gate: per-file checks +
  the cross-file rules — a target in exactly one file, in the file of its
  derived group, no backing-object conflicts — plus the reserved-name invariant
  and the nested raw ownership), `annotate_stock.py` (the `# stock N` notes),
  `gen_stats.py` (the stats generator), `mod_groups.py` (the group derivation
  shared by the validator and the migration), `gen_catalog.py` (the in-memory
  SDK catalog builder the tables and stock notes read), `gen_readme_tables.py`
  (the balance tables below).
- `dist/nemo-stats-<group>/` — the built stats mods (`hellforge-stats.json` +
  `hellforge-mod.json`, id `nemo-stats-<group>`, `gameplay: true`), one folder
  per source file. Generated; do not hand-edit.

## Build and deploy

    make -C mods/nemo/weapon_stat_tuner build    # validate -> annotate -> gen_stats
    make -C mods/nemo/weapon_stat_tuner deploy   # copy the eighteen dist mods into HellForge
    make -C mods/nemo/weapon_stat_tuner tables   # regenerate the balance tables
    make -C mods/nemo/weapon_stat_tuner regen    # force regen after a game update

`deploy` copies the eighteen `dist/nemo-stats-<group>/` folders to the HellForge
`mods/` directory (folder name = manifest id), removes the retired monolithic
`local.nemo-weapon-stat-tuner/` folder and the retired pre-split and pre-rename
folders (`nemo-stats-stratagems/`, `nemo-stats-backpacks/`,
`nemo-stats-primary-energy/`, `nemo-stats-weapons-support/`,
`nemo-stats-stratagems-support/`, `nemo-stats-weapons-utility/`, and the old
`nemo-stats-primary-*` / `nemo-stats-secondary-*` / `nemo-stats-support/` group
names), and reports the deployed file list; the launcher auto-discovers and
enables each folder. Rollback: remove the folders.

## What the stats file covers

- **Weapons** — ergonomics, sway, spread, recoil, damage (standard/durable),
  armor penetration, projectile velocity/drag, magazine capacity, reload,
  per-slot fire rate, and the laser weapons' fire status
  (`damage.status_1_type`, shipped as the numeric status enum).
- **Fire modes** — added trigger modes with the fire-mode selector on the
  left input (`fire_mode.modes.N` + `weapon_function.left`): the JAR-5
  Dominator's full-auto, the BR-14 Adjudicator's burst
  (+ `fire_mode.burst_rounds`), the P-113 Verdict's auto, and the P-2
  Peacemaker's burst; plus the rate-of-fire selector on the left input
  (`weapon_function.left`): the AR-23P Liberator Penetrator's 900 rpm
  mode, the AR-32 Pacifier's 400/700/900 rpm, and the AR-23C Liberator
  Concussive's 350/500/700 rpm
  (`fire_rate.modes.x/z`, `weapon.fire_rate`).
- **Throwables** — grenade/mine/shield/knife damage, shock, fuse, shrapnel, and
  status effects (as numeric status enums).
- **Stratagems** — orbital cooldowns (compensated for the Super Destroyer
  upgrades) and mission-uses caps.
- **Backpacks** — the GL-28 deposit capacity and the LIFT-860 Hover Pack flight
  (sustain duration/thrust, horizontal speed).
- **Explosions** — the Orbital Precision Strike and Eagle 500kg main-blast
  damage (standard + durable).
- **Boosters** — the Surplus EAT Allocation `stratagem.max_uses`.
- **Raw** — the two scope swaps (MG-43 → Sniper Scope 10x, M-105 → Combat Scope
  4x), passed through verbatim.

## Balance tables

### High-AP weapons (precision)

<!-- compare:start -->
| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AC-8 Autocannon | 325→700 | 260→350 | 190 | 30 | 4/4/4/0 | 820 | 0.3 | — | 3 | 1→0.7 | 17 | 200,450,2,100 | 2217 | 1108 |
| RS-422 Railgun | 600→800 | 225→300 | — | 35→50 | 5/5/5/5<br>→<br>5/5/5/4 | 2000 | 0.3 | 1 | 1.2 | 1→0.5 | 35→40 | 10,25,3,25 | — | — |
| RS-422 Railgun (overcharge) | 1500→2000 | 562.5→750 | — | 35→50 | 5/5/5/5<br>→<br>5/5/5/4 | 2000 | 0.3 | 1 | 1.2 | 1→0.5 | 35→40 | 10,25,3,25 | — | — |
| APW-1 Anti-Materiel Rifle | 450→690 | 225→350 | 400 | 25 | 4/4/4/0 | 880 | 0.3→0.1 | 7 | 3 | 1→0.5 | 35→40 | 20,300,2,300 | 4600 | 2333 |
| MG-206 Heavy Machine Gun | 150→220 | 35→100 | 450/600*/750 | 25→30 | 4/4/4/0<br>→<br>4/4/3/0 | 980 | 0.3→0.2 | 100 | 5.5→4 | 1 | 0→15 | 50,80,15,30 | 2750 | 1250 |
| PLAS-39 Accelerator Rifle | 250 | 125→180 | 550 | 20→15 | 3/3/3/0<br>→<br>4/4/3/0 | 1000 | 0.1 | 9→12 | 3.3→2 | 1→0.5 | 60→45 | 3,3,3,3<br>→<br>1,1,1,1 | 2292 | 1650 |
| JAR-5 Dominator | 275→325 | 90→115 | 250→350 | 35 | 3/3/3/0<br>→<br>4/4/4/0 | 180→350 | 0 | 15 | 3.7→3.3 | 0.8→0.6 | 30→40 | 30,30,50,120 | 1896 | 671 |

<!-- compare:end -->
<!-- tables:start -->
### Marksman rifles

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R-2124 Constitution | 180 | 50→80 | 60 | 20 | 3/3/3/0 | 850 | 0.3→0.2 | 5 | 2.8→1.8 | 1→0.3 | 65 | 25,25,10,60 | 180 | 80 |
| R-63 Diligence | 165 | 45→80 | 350 | 15→20 | 2/2/2/0<br>→<br>3/3/2/0 | 850 | 0.3→0.2 | 25→20 | 3.2→2.8 | 1→0.5 | 65 | 25,25,10,45<br>→<br>5,70,10,45 | 962 | 467 |
| R-2 Amendment | 200→165 | 50→80 | 480 | 20 | 2/2/2/0<br>→<br>3/3/2/0 | 850 | 0.3→0.2 | 20 | 3.5→3 | 1→0.5 | 50→55 | 25,35,10,45<br>→<br>5,70,10,45 | 1320 | 640 |
| R-72 Censor | 165 | 45→50 | 400 | 20→25 | 2/2/2/0<br>→<br>3/2/2/0 | 330 | 0.3 | — | — | 1→0.5 | 60→65 | 10,15,10,15<br>→<br>5,70,10,15 | 1100 | 333 |
| R-63CS Diligence Counter Sniper | 200→300 | 50→130 | 350 | 20→30 | 3/3/3/0<br>→<br>4/3/3/0 | 940 | 0.3→0.15 | 15→12 | 3.2→3 | 0.8→0.5 | 35→45 | 25,25,30,80<br>→<br>10,150,30,80 | 1750 | 758 |
| R-6 Deadeye | 300 | 100→130 | 100→400 | 30 | 3/3/3/0<br>→<br>4/3/3/0 | 850 | 0.3→0.15 | 8 | 2.8→2 | 1→0.5 | 65→50 | 40,40,50,200<br>→<br>5,40,50,150 | 2000 | 867 |
| R-4 Hyena | 220 | 45→90 | 190→300 | 20 | 3/3/3/0 | 950 | 0.3→0.15 | — | — | 1→0.5 | 30→40 | 30,30,50,150<br>→<br>10,150,50,150 | 1100 | 450 |

### Assault rifles

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AR-23 Liberator | 90→95 | 22→30 | 640 | 15 | 2/2/2/0 | 900 | 0.3→0.4 | — | — | 1→0.8 | 65 | 7,10,5,20 | 1013 | 320 |
| AR-23A Liberator Carbine | 90→95 | 22→30 | 920 | 15 | 2/2/2/0 | 900 | 0.3→0.4 | — | — | 1→0.8 | 70 | 14,20,6,32<br>→<br>14,25,6,32 | 1457 | 460 |
| StA-52 Assault Rifle | 90→95 | 22→30 | 790 | 15 | 2/2/2/0 | 900 | 0.3→0.4 | 56 | 4.2→3 | 1→0.8 | 55 | 10,15,6,25<br>→<br>5,5,4,12 | 1251 | 395 |
| AR-23P Liberator Penetrator | 65→72 | 15 | 640→640*/900 | 10 | 3/3/3/0 | 1000 | 0.3 | — | — | 1→0.8 | 59 | 10,15,9,22.5 | 1080 | 225 |
| AR-23C Liberator Concussive | 75 | 35 | 400→500*/700/350 | 35 | 2/2/2/2 | 800 | 0.3 | — | — | 1→0.8 | 65 | 25,25,9,30 | 875 | 408 |
| AR-32 Pacifier | 55→70 | 10 | 700→700*/900/400 | 15 | 3/3/3/0 | 900 | 0.3 | — | 3 | 1→0.8 | 60 | 15,20,10,25 | 1050 | 150 |
| AR-59 Suppressor | 80→90 | 20 | 850 | 10→20 | 2/2/2/0 | 330 | 0.3 | — | — | 1→0.8 | 60 | 7,14,6,26 | 1275 | 283 |
| AR/GL-21 One-Two | 95 | 24→30 | 650 | 15 | 2/2/2/0 | 920 | 0.3 | 40 | 3.3 | 1→0.6 | 30→45 | 10,15,8,20 | 1029 | 325 |
| AR-11 Arbitrator | 70→95 | 20→30 | 1200 | 15 | 2/2/2/0 | 920 | 0.3 | 45 | 3.8→3 | 1→0.6 | 30→45 | 10,15,8,20 | 1900 | 600 |
| VG-70 Variable | 85→95 | 23→30 | 300/550*/750 | 10→15 | 2/2/2/0 | 320 | 0.6→0.4 | 49 | 3.6→3 | 1→0.6 | 25→45 | 5,10,4,8 | 1188 | 375 |
| AR-2 Coyote | 75→95 | 10→30 | 600→500 | 12→15 | 3/3/3/0 | 650→718 | 0.3→0.25 | 45→30 | 3 | 1→0.7 | 50 | 17,20,6,36<br>→<br>26,65,6,36 | 792 | 250 |
| BR-14 Adjudicator | 95→150 | 23→70 | 550 | 15→20 | 3/3/3/1 | 820 | 0.3→0.2 | 30→25 | 3 | 1→0.7 | 40 | 17,35,6,50<br>→<br>40,100,6,35 | 1375 | 642 |
| MA5C Assault Rifle | 90→150 | 16→70 | 640 | 15→20 | 3/3/3/0 | 820 | 0.3→0.2 | 32→25 | 3.2 | 1→0.7 | 60→40 | 12,20,12,30<br>→<br>40,100,12,30 | 1600 | 747 |
| AR-61 Tenderizer | 105→180 | 30 | 600*/850 | 15→25 | 2/2/2/0 | 820 | 0.3→0.2 | 35→25 | 3.3 | 1→0.6 | 65→45 | 7,7,5,13<br>→<br>22,85,5,13 | 2550 | 425 |

### SMGs

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MP-98 Knight | 90→95 | 18 | 1380 | 10→15 | 2/2/2/0 | 375 | 1.2→0.6 | — | — | 1→0.9 | 90 | 10,20,2.5,15 | 2185 | 414 |
| StA-11 SMG | 90→95 | 18 | 1050→1200 | 10→15 | 2/2/2/0 | 375 | 1.2→0.6 | 48 | 3.5 | 0.7 | 80 | 10,20,5,10 | 1900 | 360 |
| M7S SMG | 90 | 18 | 872→1200 | 10→15 | 2/2/2/0 | 320 | 1.2→0.6 | 48 | 3 | 1→0.9 | 90 | 7,14,2.5,10<br>→<br>2,4,1,4 | 1800 | 360 |
| SMG-203 Gallant | 65→75 | 13 | 1380→450 | 10→15 | 3/3/3/0 | 450 | 1.2→0.6 | — | — | 1→0.9 | 80 | 15,24,2.5,18 | 562 | 98 |
| SMG-72 Pummeler | 85→120 | 17 | 475→500 | 15→30 | 2/2/2/0 | 210 | 1.2→0.6 | — | — | 1→0.9 | 90 | 10,10,5,10 | 1000 | 142 |
| SMG/FLAM-34 Stoker | 130→120 | 30→17 | 420→500 | 15→30 | 2/2/2/0 | 285 | 1.2→0.6 | — | — | 1→0.9 | 60 | 10,5,5,15 | 1000 | 142 |
| SMG-32 Reprimand | 140 | 32 | 490 | 15→35 | 3/3/3/0<br>→<br>3/3/2/0 | 285 | 1.2→0.7 | 25→30 | 3.5→2.7 | 1→0.9 | 55→40 | 25,40,6,55 | 1143 | 261 |

### Pistols

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P-19 Redeemer | 70→95 | 12→18 | 1100 | 10→15 | 2/2/2/0 | 375 | 1.2→0.6 | — | — | 1→0.5 | 95 | 20,20,5,10 | 1742 | 330 |
| P-2 Peacemaker | 100→95 | 32→18 | 900→1200 | 10→15 | 2/2/2/0 | 320 | 1.2→0.6 | — | — | 1→0.5 | 100 | 20,40,3,15 | 1900 | 360 |
| P-113 Verdict | 140 | 32 | 450 | 15 | 3/3/3/0 | 285 | 1.2→0.8 | 10→18 | 2 | 1→0.5 | 100 | 20,50,10,45 | 1050 | 240 |
| P-69 Veto | 105→140 | 35 | 750 | 35 | 3/3/3/0 | 375 | 0 | 12 | 3.1→1.8 | 1→0.5 | 100 | 20,50,5,45 | 1750 | 438 |
| P-92 Warrant | 80→115 | 20→30 | 450 | 15 | 3/3/3/0 | 285 | 0 | 13→18 | 2 | 1→0.5 | 100 | 20,50,10,45 | 862 | 225 |
| M6C/SOCOM Pistol | 125→180 | 28→50 | 900 | 15 | 2/2/2/0<br>→<br>3/3/2/0 | 285 | 1.2→0.8 | 12 | 1.5 | 1→0.5 | 100 | 20,40,3,15<br>→<br>20,40,3,45 | 2700 | 750 |
| P-4 Senator | 225→300 | 75→125 | 200 | 20 | 4/4/4/0 | 550 | 1.2→0.8 | 6 | 4.5→3 | 1→0.5 | 75 | 20,50,3,50 | 1000 | 417 |
| P/40-K Bolt Pistol | 325 | 115 | 150 | 35 | 4/4/4/0 | 350 | 0 | 6 | 2.4 | 1→0.5 | 30→45 | 100,500,200,500 | 812 | 288 |

### Shotguns

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | Pellets | Tot std | Tot dur | Start | Spare | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M90A Shotgun | 55→71 | 20→43 | 80 | 35 | 2/2/2/0 | 385 | 0.5→0.4 | 6→8 | 2.2 | 1 | 65 | 40,40,50,200 | 11 | 605→781 | 220→473 | 24→32 | 44→60 | 1041 | 631 |
| SG-8 Punisher | 45→49 | 12→30 | 80 | 35 | 2/2/2/0 | 385 | 0.5 | 8 | 2.4→2 | 1 | 65 | 40,40,50,200 | 9→16 | 405→784 | 108→480 | 32 | 60 | 1045 | 640 |
| SG-8S Slugger | 330→500 | 90→250 | 80 | 30→35 | 3/3/3/0 | 390 | 2→0.4 | 8 | 2.4→2 | 1→0.7 | 65 | 40,40,50,200 | 1 | 330→500 | 90→250 | 32 | 60 | 667 | 333 |
| SG-451 Cookout | 16→24 | 3→6 | 80 | 35→30 | 2/2/2/0 | 120 | 0.8 | 8 | 2.4→2 | 1 | 65 | 35,35,50,165 | 20 | 320→480 | 60→120 | 32 | 60 | 640 | 160 |
| SG-20 Halt | 35→54 | 10→22 | 80 | 20 | 3/3/3/0 | 385 | 0.3 | 8 | 2.4→2 | 1 | 65 | 40,40,50,200 | 11 | 385→594 | 110→242 | 32 | 60 | 792 | 323 |
| SG-97 Sweeper | 42→54 | 11→21 | 150 | 20 | 3/3/3/0 | 385 | 0.3 | 7 | 2.2 | 1 | 65 | 65,40,50,150 | 12 | 504→648 | 132→252 | 46 | 70 | 1620 | 630 |
| SG-225 Breaker | 30→46 | 6→22 | 300 | 15 | 2/2/2/0 | 360 | 0.5 | — | — | 1 | 65 | 23,35,35,80 | 11 | 330→506 | 66→242 | — | — | 2530 | 1210 |
| SG-225SP Breaker Spray&Pray | 15→23 | 4→9 | 330 | 3 | 2/2/2/0 | 250 | 0.5 | — | — | 1 | 65 | 35,35,35,55 | 16 | 240→368 | 64→144 | — | — | 2024 | 792 |
| SG-225IE Breaker Incendiary | 20 | 10 | 300 | 10 | 2/2/2/0 | 120 | 0.8 | — | — | 1 | 65 | 20,25,25,60 | 12 | 240 | 120 | — | — | 1200 | 600 |
| DBS-2 Double Freedom | 70→105 | 35→74 | 650 | 35 | 3/3/3/0 | 385 | 0.5→0.4 | 2 | 2.4→2 | 1 | 65 | 60,120,70,400 | 12 | 840→1260 | 420→888 | 22 | 40 | 13650 | 9620 |

### Laser weapons

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | Beams | Fire str | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LAS-99 Quasar Cannon | 2000 | 2000 | 10*/10 | 50 | 6/6/6/3 | 1300 | 0 | — | — | 1→0.7 | 35 | 40,40,50,180 | — | 0 | 333 | 333 |
| R/40-K Hot-Shot Marksman Rifle | 275 | 40→30 | 210→1000 | 20→15 | 3/3/3/0<br>→<br>3/2/2/0 | 500→2000 | 0 | 12 | 2.7→3 | 1→0.5 | 30→40 | 12.5,17.5,12.5,32.5<br>→<br>0.1,0.1,0.1,0.1 | — | 0→16 | 4583 | 500 |
| LAS-58 Talon | 200 | 20 | 750 | 10 | 3/3/3/0<br>→<br>2/2/2/0 | 1300→2000 | 0 | — | 4.6→3 | 1→0.5 | 95 | 2,2,2,1<br>→<br>0.1,0.1,0.1,0.1 | — | 0→4 | 2500 | 250 |
| LAS-16 Sickle | 60→70 | 6 | 750→850 | 10 | 2/2/2/0 | 1300→2000 | 0 | — | 2.8 | 1→0.7 | 65 | 2,2,1,2<br>→<br>0.1,0.1,0.1,0.1 | — | 0→0.7 | 992 | 85 |
| LAS-17 Double-Edge Sickle | 60→70 | 6 | 700 | 10 | 2/2/2/0 | 1300→2000 | 0 | — | 2.8 | 1→0.7 | 65 | 2,2,1,2 | — | 0→0.7 | 817 | 70 |
| LAS-13 Trident | 60→70 | 6 | 300→250 | 10→15 | 2/2/2/0 | — | — | — | 3.7 | 1→0.7 | 65→45 | 2,2,1,2<br>→<br>0.1,0.1,0.1,0.1 | 3 | 0→0.7 | 875 | 75 |
| LAS-12 Sai | 80→70 | 4→6 | 800 | 10 | 3/3/3/0<br>→<br>2/2/2/0 | 100→2000 | 0 | — | 1.8 | 1→0.8 | 65 | 8,8,2,25<br>→<br>0.1,0.1,0.1,0.1 | — | 0→0.7 | 933 | 80 |
| LAS-98 Laser Cannon | 350→450 | 200→420 | — | 0→10 | 4/4/4/4 | — | — | — | 5 | 1→0.5 | 45 | 0,0,0,0 | — | — | — | — |
| LAS-5 Scythe | 350→450 | 70→75 | — | 0 | 2/2/2/0 | — | — | — | 3.7 | 1→0.7 | 65 | 0,0,0,0 | — | 1 | — | — |
| LAS-7 Dagger | 250→300 | 50 | — | 0 | 2/2/2/0 | — | — | — | 2.3 | 1→0.5 | 95 | 0,0,0,0 | — | 1 | — | — |

### Plasma weapons

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PLAS-39 Accelerator Rifle | 250 | 125→180 | 550 | 20→15 | 3/3/3/0<br>→<br>4/4/3/0 | 1000 | 0.1 | 9→12 | 3.3→2 | 1→0.5 | 60→45 | 3,3,3,3<br>→<br>1,1,1,1 | 2292 | 1650 |
| PLAS-1 Scorcher | 100 | 50 | 350→500 | 20 | 2/2/2/0 | 550 | 1.5 | 20→30 | 2.5 | 1→0.7 | 65 | 20,20,2,20 | 833 | 417 |
| PLAS-101 Purifier | 200 | 100 | 1000 | 20 | 3/3/3/0 | 350→550 | 1.5→1 | 15→20 | 2.5 | 1→0.7 | 65 | 20,20,2,20 | 3333 | 1667 |
| PLAS-15 Loyalist | 100 | 50 | 1000 | 20 | 2/2/2/0 | 550 | 1 | — | 1.8 | 1 | 95 | 2.5,10,2.5,10 | 1667 | 833 |
| SG-8P Punisher Plasma | 0 | 0 | 80 | 20 | 2/2/2/0 | 90→250 | 4 | 10 | 2.5 | 1 | 65 | 40,40,50,180 | 0 | 0 |
| PLAS-45 Epoch | 400 | 200 | — | 30 | 4/4/4/4 | 250→550 | 0.1 | 3→7 | 4 | 1 | 25→40 | 20,45,15,65 | — | — |

### Special weapons

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| JAR-5 Dominator | 275 | 90 | 250→350 | 35 | 3/3/3/0 | 180 | 0 | 15 | 3.7→3.3 | 0.8→0.6 | 30→40 | 30,30,50,120 | 1604 | 525 |
| ARC-3 Arc Thrower | 250 | 100→250 | — | 35 | 7/7/7/0 | — | — | — | — | 1→0.7 | 50 | 40,40,50,50 | — | — |
| P-35 Re-Educator | 60 | 10 | 110→300 | 1 | 4/4/3/0 | 150 | 2 | 6 | 2.1 | 1→0.5 | 100 | 5,15,5,15 | 300 | 50 |

### Machine guns

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M-105 Stalwart | 90→95 | 22→30 | 700/850*/1150 | 15 | 2/2/2/0 | 900 | 0.3→0.4 | 250 | — | 1→0.7 | 40 | 15,15,10,20 | 1821 | 575 |
| MG-43 Machine Gun | 90→150 | 23→70 | 630/760*/900 | 20 | 3/3/3/1<br>→<br>3/3/2/1 | 820 | 0.3→0.2 | 175 | 4.5→3 | 1→0.7 | 15→25 | 20,20,15,30 | 2250 | 1050 |
| M-1000 Maxigun | 80→150 | 18→75 | 1500 | 15 | 3/3/3/0<br>→<br>3/3/2/0 | 920 | 0.3→0.2 | — | 4.5 | 1 | 4→15 | 20,20,15,30<br>→<br>25,10,20,15 | 3750 | 1875 |
| MG-206 Heavy Machine Gun | 150→220 | 35→100 | 450/600*/750 | 25→30 | 4/4/4/0<br>→<br>4/4/3/0 | 980 | 0.3→0.2 | 100 | 5.5→4 | 1 | 0→15 | 50,80,15,30 | 2750 | 1250 |

### Cannons

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| APW-1 Anti-Materiel Rifle | 450→690 | 225→350 | 400 | 25 | 4/4/4/0 | 880 | 0.3→0.1 | 7 | 3 | 1→0.5 | 35→40 | 20,300,2,300 | 4600 | 2333 |
| RS-422 Railgun | 600→800 | 225→300 | — | 35→50 | 5/5/5/5<br>→<br>5/5/5/4 | 2000 | 0.3 | 1 | 1.2 | 1→0.5 | 35→40 | 10,25,3,25 | — | — |
| AC-8 Autocannon | 325→700 | 260→350 | 190 | 30 | 4/4/4/0 | 820 | 0.3 | 10 | 3 | 1→0.7 | 17 | 200,450,2,100 | 2217 | 1108 |
| R-36 Eruptor | 230 | 115 | 32 | 35 | 4/4/4/0 | 180 | 0 | 5 | 4.7 | 0.8→0.6 | 25→40 | 30,30,50,120 | 123 | 61 |

### Rockets

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GR-8 Recoilless Rifle | 3200 | 3200 | 600 | 50 | 6/6/6/3 | 250 | 0.3 | 1 | 6→4 | 1→0.9 | 10 | 40,40,50,180 | 32000 | 32000 |
| FAF-14 Spear | 4000→5000 | 4000→5000 | 240 | 50 | 7/7/7/7<br>→<br>12/12/12/12 | — | — | 1 | 5→4 | 1 | 10 | 2.5,10,2.5,10 | 20000 | 20000 |
| RL-77 Airburst Rocket Launcher | 350 | 350 | 600 | 50 | 3/3/3/0 | 250 | 0.3 | 1 | 5→4 | 1 | 10 | 40,40,50,180 | 3500 | 3500 |
| GP-20 Ultimatum | 1000 | 1000 | 900 | 50 | 6/6/6/6 | 20→60 | 0.5 | 1 | 2.7 | 1 | 35 | 20,50,3,50<br>→<br>20,50,3,500 | 15000 | 15000 |
| P-34 Breacher | 60 | 0 | 20 | 10 | 4/4/3/0 | 150 | 2 | 1 | 2.7→1.8 | 1 | 45 | 200,500,100,450 | 20 | 0 |
| P-33 Missile Pistol | 1000 | 1000 | 60 | 40 | 5/5/5/0 | 1 | 0 | 1 | 2.7→1.8 | 1 | 45 | 200,500,100,450 | 1000 | 1000 |
| MLS-4X Commando | 1100→1650 | 1100→1650 | 240 | 40 | 6/6/6/3 | — | — | 4 | — | 1 | 10 | 2.5,10,2.5,10 | 6600 | 6600 |

### Grenade launchers

| Weapon | Std | Dur | RPM | Stg | AP | Vel | Drag | Cap | Reload | Sway | Ergo | Drift/Climb (H/V) | DPS | dDPS |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GL-21 Grenade Launcher | 20→250 | 2→250 | 160 | 30 | 0/0/0/0 | 100 | 1.2 | 10 | 3.5 | 1→0.7 | 25 | 170,175,60,90<br>→<br>90,95,60,90 | 667 | 667 |
| GL-52 De-Escalator | 20→250 | 2→250 | 200 | 30 | 0/0/0/0 | 100 | 1.2 | 6 | 2.5 | 1→0.7 | 25 | 90,95,60,90 | 833 | 833 |
| GL-28 Belt-Fed Grenade Launcher | 0 | 0 | — | 30 | 4/4/4/0 | 100 | 1.2 | — | 4.5 | 1→0.8 | 20→45 | 20,25,15,35 | — | — |
| GL-15 Evictor | 50 | 2 | 60 | 30 | 3/3/3/0 | 100 | 1.2 | 4 | 2.7 | 1 | 65 | 40,40,50,200 | 50 | 2 |
| GP-31 Grenade Pistol | 250 | 250 | 900 | 40 | 3/3/3/0 | 100 | 1.2 | 1 | 1.7 | 1→0.8 | 95 | 20,50,3,50 | 3750 | 3750 |

### Throwables

| Weapon | Std | Dur | In | Out | Shock | Fuse | Start | Max | Shrapnel | Status | Direct | Shield |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| G-12 High Explosive | 800→1200 | 800→1200 | 2.5 | 7 | 9 | 3.5→4 | 4 | 5→6 | — | — | — | — |
| G-16 Impact | 400→1200 | 400→1200 | 2.5 | 7 | 8 | — | 4 | 5→6 | — | — | — | — |
| G-50 Seeker | 500→1200 | 500→1200 | 3.5→2.5 | 7 | 8 | — | 4 | 5 | — | — | — | — |
| G-6 Frag | 500→300 | 500→300 | 4 | 10 | 14 | 2.4 | 4 | 6 | 35→64 | — | 110→180 | — |
| G-7 Pineapple | 300→200 | 300→200 | 4 | 10 | 14 | 2.4→2.2 | 4 | 5 | 18→24 | — | — | — |
| G-123 Thermite | 2000 | 2000 | 1.5 | 2.5 | 4 | 2.9 | 2 | 3→4 | — | — | — | — |
| G-60 Anti-Tank Seeker | 1800→3000 | 1800→3000 | 4→2 | 12→3 | 15 | — | 2 | 3→4 | — | — | — | — |
| G-48 Giga Grenade | 2000→2400 | 2000→2400 | 2→4 | 12 | 16 | — | 2 | 2→3 | — | — | — | — |
| G-10 Incendiary | 300 | 300 | 1 | 7 | 9 | 2.9→2 | 4 | 5→6 | — | fire 50→100 | — | — |
| G-13 Incendiary Impact | 150→300 | 150→300 | 1 | 7 | 9 | — | 4 | 5→6 | — | fire 100 | — | — |
| G-8 Immolation | 20 | 20 | 4 | 10→12 | 10 | — | 4 | 6 | — | fire 100 | — | — |
| G-142 Pyrotech | 50 | 50 | 2.5 | 5→6 | 7 | 2.9→2.4 | 4 | 6 | — | fire 100 | — | — |
| G-23 Stun | 0 | 0 | 1 | 10→12 | 15 | 1.8→1.4 | 4→5 | 5→7 | — | stun-large→stun-massive 25 | — | — |
| G-109 Urchin | 0 | 0 | 2→4 | 4→12 | 1 | 2.9→3 | 4→5 | 5→7 | — | stun-large→stun-massive 10 | — | — |
| G-31 Arc | 0 | 0 | 1 | 10 | 15 | 3 | 4 | 5 | — | arc-stun-small 8 | 100→150 | — |
| G-3 Smoke | — | — | 8→16 | 8→16 | 0 | 2.4→2 | 4→6 | 5→7 | — | — | — | — |
| G-89 Smokescreen | — | — | 5→16 | 5→16 | 0 | — | 4→6 | 5→7 | — | — | — | — |
| TM-1 Lure Mine | 1000→1200 | 1000→1200 | 2→4 | 8→12 | 12 | — | 3 | 4 | 35 | — | 110→180 | — |
| G/40-K Melta Mine | 2000→3000 | 2000→3000 | 2.5 | 6 | 15 | — | 3 | 4 | — | — | — | — |
| G/SH-39 Shield | — | — | — | — | — | — | 3 | 4→5 | — | — | — | 1.8→2.2 / 1000→2000 |

### Vehicle weapons

| Weapon | Cap | Start | Spare | Supply | Drift H | Drift V | Climb V |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M-102 Gunner FRV / gun | 100→1000 | 4→1 | 4→0 | 2→0 | 4 | 4 | 5 |

<!-- tables:end -->

The LAS-13 Trident is a beam weapon: its 3 barrels fire one beam each (3
parallel beams), so its DPS/dDPS are the per-beam damage × beam fire rate / 60 × 3
(the beam fire rate is a tunable field; the mod sets it to 350 rpm).
The other lasers are hitscan/projectile and use the standard damage × RPM / 60.
Multi-rate weapons (e.g. MG-206, VG-70, M-105) show their DPS/dDPS at the
highest rate slot.

## Gotchas (read before changing a stat)

- Shared fields (derived from the catalog) affect co-sharers; the validator lists
  each one's co-sharers, so check them before changing a shared stat.
- **The orbital strike cooldowns are compensated for the Super Destroyer upgrades.**
  The written base is `round(target / 0.855)` so the effective cooldown hits the
  target only with both upgrades active (Zero G Breech Loading + Moral Augmentation);
  without them the cooldown is the full (higher) base.
- **The Commando cooldown is compensated for Moral Augmentation only.** As a
  team-weapon call-in it is not affected by the −10% Orbital upgrade, so its base is
  `round(target / 0.95)` (60→63), not the orbital `round(target / 0.855)`.

## Pointers

- Build: `make -C mods/nemo/weapon_stat_tuner build`.
- Deploy: `make -C mods/nemo/weapon_stat_tuner deploy`.
- Validate the source files: `uv run mods/nemo/weapon_stat_tuner/scripts/validate_stats.py`.
- Regenerate the balance tables: `make -C mods/nemo/weapon_stat_tuner tables`.
