# Public Release Notes

This repository is being organized for public research access.

## What is public here

- research rationale and method-development history;
- ROS/PMFS-derived research code captured in `ros2_package/`;
- offline replay/evaluation scripts;
- compact evidence, manifests and checksums;
- selected frozen binaries/evidence archives already committed to Git.

## What is not bundled

The original VGR/GADEN House scenario data used by the runners are external
and are not committed to this repository.

The VM-specific absolute paths visible in scripts/manifests are
reproducibility records from the original experimental environment; they are
not credentials.

## Upstream and licensing note

`ros2_package/package.xml` identifies the captured `gsl_server` package as
GPLv3 and names its upstream maintainer. The repository also contains
third-party/upstream-derived components.

Making this repository public should not be interpreted as a claim that every
line in `ros2_package/` was authored by this project, nor as relicensing
external datasets or third-party components.

Users should preserve applicable upstream notices and licenses.

## Security/privacy scan performed before public release

A repository code search was performed for common accidental secret patterns
such as GitHub tokens, AWS credentials, OpenAI keys, passwords and private-key
headers. No obvious credential string was found in the indexed default-branch
files. This is a best-effort repository scan, not a guarantee about every
historical Git object.

## Scientific-status note

Historical ME-ACI evidence and the newer TNQC research cycle are deliberately
kept separate.

TNQC's authoritative six-case 300-s online-representation localization result
is still pending; the most recent attempted run stopped before scientific
execution because of environment/infrastructure failure.
