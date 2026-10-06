# Independent local components

## ASCi/sci

- Path: `ASCi/sci`
- Management: independent local repository
- Root submodule: no
- Child Git directory: `ASCi/sci/.git` (independent directory)
- Child HEAD observed for this repair: `803f46ecb129ceca971b41c1efc045ab812d5a50`
- Child branch observed for this repair: `master`
- Remote observed for this repair: none configured
- Observation date: 2026-10-05 (America/Los_Angeles)

The root repository does not track this component's contents or a Gitlink.
Its existing history, index, modified/deleted/untracked files, and local Git
directory remain managed within the child repository. Do not run root submodule
initialization, synchronization, reset, clean, or checkout operations on it.

The HEAD above is an identity snapshot, not a lockfile or instruction to reset
the child. Back up this independent repository separately when relocating or
replacing root Git metadata; a root clone does not restore the local component.
