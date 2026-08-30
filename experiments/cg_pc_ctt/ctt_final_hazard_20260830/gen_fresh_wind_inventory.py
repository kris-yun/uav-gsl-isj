#!/usr/bin/env python3
"""Deterministic generator for the CTT H01 FRESH_WIND_INVENTORY provenance JSON.

Reads the authoritative wind CSV SHA-256 table (one line per primary wind CSV)
and the map/scene hashes, attaches the consumption status derived from the
frozen CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1 manifest, and emits the inventory
JSON together with its SHA-256.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(r"D:\ZYC\uav-gsl-isj")
OUT_DIR = REPO / "experiments" / "cg_pc_ctt" / "ctt_final_hazard_20260830"
OUT_JSON = OUT_DIR / "FRESH_WIND_INVENTORY_20260830.json"

# map/scene (House01) hashes, computed on 2026-08-30 from the shared folder.
MAP_HASHES = {
    "OccupancyGrid3D.csv": "846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb",
    "occupancy.pgm": "41922bd418b6b48dd6e2525783269be76a495322fffe37920f63b6fcc402f646",
    "occupancy.yaml": "291dcbdf9bde61874ebd3a0139b0948d8d53a452a313401bcd70646120e4b31f",
}

# full SHA-256 table: config -> {frame_index: sha256}
WIND_HASHES = {
    "1,3-2,4_fast": {
        0: "34e716bea6b8d8df882fa8ec9b65ae081d7584f118aeb4778b77495fb34a9165",
        1: "89300004178fda68b3f52e74368fd6545e8cce136dc570dce92fd183443e1bfc",
        2: "05e4dedc9d54f75fd998fb68a22f94d664d97a0cd1075415d179d1fc1b75b846",
        3: "51ade5681db2836e64910f118de742082de1b2dc2450b64079d050d819a3cc30",
        4: "d0ff85015f83f1ec21619e7b6e26652a4a07e25c9abb560ab4c705fc9e97f519",
        5: "171bc17445dcd3195cd4869a8cfec67dce03518d406ae7363a5745991424b2ee",
        6: "3b5075eecea5d6ee183d06f2a4b128abeec96dd2b8f5fc3e08ef93436495adec",
        7: "d40bd954f8f664fcac72ab183e74cc9052e1cfabd8176a4e3bb304478527e980",
        8: "f784e39cadf1f7b10ee85803699ceeb129e34ba841677bfe3ed7c53e2f507830",
        9: "a5a85efe26e303a0c2bee4e0798409e99e8323d0e57da0342f8f610bc03a3ab7",
        10: "7eef12223369fd723cad2da7b335dcdb3a8e723acde65fda929cd4913b8a2c44",
    },
    "1,3-2,4_slow": {
        0: "1ca92bb77ab86fd9678b8990526a48a5d593499e6619e0264dfa47fbf053d553",
        1: "b059b9f8604f64f6907f46e4e7d46c1b8667fe0b0c8fb93f29cd558e69cc3639",
        2: "1c29ffea53ecb7818077a2eadef7cdca75f78ddcfe1d30f29e554dcd0ca730e0",
        3: "c574e8823c66a13cc2c26f7e923efa5fdc73268feddb4df52e5bd10452441e41",
        4: "bd5b778f442c1f65693f355077f3981459ae998bc4e2ed159ace68e83c0bb195",
        5: "0782715472ec7117a7ae83a5d167bf2e9e8ad60cdd741e23b40b972abec0a3e6",
        6: "ff3e5130965b773d4bded4263cf7797286f935d11b1fcc91288ebce0fe358e2e",
        7: "f2c9925939830122bdbe255c7bdbd7bc4d04dcc5fd979937cf754d2c994a1876",
        8: "10ee36605e18c17b757a4daad82d6068d0ba310db782227c92fe689bbe6314ed",
        9: "78e11400e8ede03855a53610331a05f24781ebc9885b60854c635a084c4b759c",
        10: "45889f55e8dad5e8351b73a95b2a35d63a3be0543cdf869b54ce3f32bcce92c2",
    },
    "2,4-1_fast": {
        0: "34e716bea6b8d8df882fa8ec9b65ae081d7584f118aeb4778b77495fb34a9165",
        1: "62a36503ef257e2218346093221615e9e33c3ddf563893f40a9e6e17227ee555",
        2: "232fee47e75c2f43ef6e879593cde1fe90a2978031e7a5378b4c64fea3059d00",
        3: "beea3d750a405137be4e8a53e1af4b24b617bbd94553cef74f9f434e5d520b5b",
        4: "6f5a94c11b58e14639afa234f4d39c518924496301aa9a2888857a71a3118054",
        5: "a06fa2161d0cffd010c9c7507ce054a9953cea53337de711142dca6b7c29fac7",
        6: "131fb7e5da281d5d1944e19451bdeef5ccb58aab2f24cde8185009072626d442",
        7: "7ec54d8837ed07b1480589bc2024d343717154f9fe27d75e6bf1341ffd851be3",
        8: "37503b1ba4f8491b5124526a67c1e58b8349de26874ab481a3ddf32811699612",
        9: "9c3b6916a373e78ea0bed69ed55e425091c7e328f1be412beebc4771e2d9f822",
        10: "5d8329b32441348d0f8278d196cbb33aff2e59cabc25ba0cbceea1e4235d6923",
    },
    "2,4-1_slow": {
        0: "34e716bea6b8d8df882fa8ec9b65ae081d7584f118aeb4778b77495fb34a9165",
        1: "5f444221ad19876126b4ce46e1995e9d878134683386e73079d080ba6e09e6b6",
        2: "3d545bdbafbc44d7caefec38354b69fa1de309b39bd8afe751d70ef3d3c00939",
        3: "31f55f30a33b9e7d7c5643e0527684f7ab625587446a9fa842e0a68a1d9cd7f6",
        4: "636233416b69cb22f490b5571a6acf89ecb43348af4743290f0ad2c9078d91da",
        5: "c14a79318dc067cea68806b60e63e8fd115bc226624cf7e1ce8879663d0ebfd4",
        6: "9a907236160ac7f0a751a8f62f9e509dc0b5d17a75a05d579cfe16e96d26b23c",
        7: "3a48360efc66559c8b482821ce28875b053ae5e8e9fc2de880e1299808a2de18",
        8: "a4a37503312eda8b8e75249bd5a2d0dded898554f603bb219d702b0c95aef641",
        9: "634c51073107b6856d93a79c156982f9be399355d370222c78bc710fa33fbf51",
        10: "bf541b79ac60c2ea5fda1c6181fcccac0a2fd1a9a217ea2c7cb20adba5c3fe63",
    },
}

# wind direction/speed semantics (from GADEN House01 naming)
CONFIG_SEMANTICS = {
    "1,3-2,4_fast": {"direction": "1,3 -> 2,4", "speed": "fast"},
    "1,3-2,4_slow": {"direction": "1,3 -> 2,4", "speed": "slow"},
    "2,4-1_fast": {"direction": "2,4 -> 1", "speed": "fast"},
    "2,4-1_slow": {"direction": "2,4 -> 1", "speed": "slow"},
}

# consumption mapping from CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1:
# context c (0..9) uses 2,4-1_fast frame (c+1); frame 0 unused.
# split from prepare_ctt_h01_native_wind_contexts.py SPLIT dict.
SPLIT = {0: "train", 1: "test", 2: "test", 3: "train", 4: "validation",
         5: "train", 6: "train", 7: "validation", 8: "train", 9: "train"}

# binary wind_iteration -> original CSV frame correspondence, confirmed by
# byte-level converter re-run on 2026-08-30 (cells=327294).
BINARY_HASHES = {
    0: "106d8da07e4b92afb390fbb292891a10c2539e10b1b777f76da54fce6f7b261d",
    1: "c9f9d44a81753aef5d4ad82ad9ccd710ab1c6d0646171eec6e330c4e25317212",
    2: "7077e5deae400299465fbb28287c7a5c759bae70bb37d82f3587f9a8822edc29",
    3: "a314adf03b856995ae03891835afcddbe93c4074471683e9ad42c0f8e770c048",
    4: "1df0613ec86d0830a5f40f126960f41712ea7c66e617f2568df0c494decdc0c9",
    5: "6048ca231b56593d398fac5047f53138b884f7db0487b4953b2ce5215294bf06",
    6: "fe61217b6cae64e7a27e59da2cfbc6ad7115f9a6a1c6b5834d5d1e7765191b4b",
    7: "dccfe0ad0bb0af9b132f587d7a93f4885f59446c359300c00951a3bb8d78e995",
    8: "e621dad08061c9b7520ee9e0db8e4927c0cc7321d0addec56ce567754c2f1ef9",
    9: "a0b870560ef5541819c1c2c0d6e1876f9f8a2711a895d0552705592529c1d043",
    10: "3d161a7ac1230788bec1aa2ae56f5b465ac2c872ed1bf2c7f244159330e8d69a",
}

# fresh binary wind_iteration hashes from converter verification run (fresh configs).
FRESH_BINARY_HASHES = {
    "1,3-2,4_fast": {1: "768a49c2be67dec6", 10: "447b7816f91350fe"},
    "1,3-2,4_slow": {1: "7665cbc84a3aaec9", 10: "2ef2ff75d0151428"},
    "2,4-1_slow": {1: "3fa664c21fd1fa40", 10: "b9ec9b069015a5e3"},
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    contexts = []
    for context in range(10):
        contexts.append({
            "context": context,
            "split": SPLIT[context],
            "source_config": "2,4-1_fast",
            "source_frame": context + 1,
            "binary_wind_iteration": context + 1,
            "binary_sha256": BINARY_HASHES[context + 1],
            "csv_sha256": WIND_HASHES["2,4-1_fast"][context + 1],
        })

    configs = []
    fresh_frames = []
    for config in sorted(WIND_HASHES):
        frames = []
        for frame in sorted(WIND_HASHES[config]):
            csv_sha = WIND_HASHES[config][frame]
            if config == "2,4-1_fast" and frame in range(1, 11):
                consumed_by = f"CTT context {frame - 1} (split {SPLIT[frame - 1]})"
                eligible = "NO"
                reason = f"consumed as CTT native wind context {frame - 1}"
            elif config == "2,4-1_fast" and frame == 0:
                consumed_by = None
                eligible = "YES"
                reason = "2,4-1_fast frame 0 never mapped to any CTT context (wind_iteration_0 unused)"
            else:
                consumed_by = None
                eligible = "YES"
                reason = "independent House01 CFD wind config never used for CTT neural M1"
            frames.append({
                "frame": frame,
                "csv_sha256": csv_sha,
                "consumed_by": consumed_by,
                "eligible_fresh": eligible,
                "reason": reason,
            })
            if eligible == "YES":
                fresh_frames.append({
                    "config": config,
                    "frame": frame,
                    "csv_sha256": csv_sha,
                    "semantics": CONFIG_SEMANTICS[config],
                })
        configs.append({
            "config": config,
            "semantics": CONFIG_SEMANTICS[config],
            "frames": frames,
        })

    inventory = {
        "contract": "CTT_H01_FRESH_WIND_INVENTORY_V1",
        "date": "2026-08-30",
        "house": "House01",
        "vmware_share": {
            "windows_host_path": "D:\\ZYC\\A-gas\\workspace",
            "vm_guest_path": "/mnt/hgfs/workspace",
            "vm_hostname": "zyc-virtual-machine",
            "vm_ssh": "zyc@192.168.111.128",
            "wind_csv_root_win": "D:\\ZYC\\A-gas\\workspace\\GADEN_files\\scenarios\\House01\\wind_simulations",
            "wind_csv_root_vm": "/mnt/hgfs/workspace/GADEN_files/scenarios/House01/wind_simulations",
            "native_wind_root_vm": "/home/zyc/rmfe_cl_env/H01/wind",
            "context_manifest_vm": "/home/zyc/CTT_H01_NATIVE_WIND_CONTEXTS_20260830/context_manifest.json",
        },
        "map_scene_sha256": MAP_HASHES,
        "converter": {
            "binary": "/home/zyc/rmfe_wind_converter_install_v4/rmfe_wind_converter/lib/rmfe_wind_converter/rmfe_wind_converter",
            "source": "/home/zyc/rmfe_wind_converter_src/rmfe_wind_converter.cpp",
            "cells": 327294,
            "frames_per_config": 11,
            "verification": "byte-level re-run of 2,4-1_fast on 2026-08-30 reproduces existing wind_iteration_* hashes exactly",
        },
        "consumed_contexts": contexts,
        "configs": configs,
        "summary": {
            "total_configs": 4,
            "total_frames": 44,
            "consumed_frames": 10,
            "consumed_desc": "2,4-1_fast frames 1..10 = CTT contexts 0..9",
            "fresh_eligible_frames": len(fresh_frames),
            "distinct_fresh_frames_note": "frame 0 is byte-identical across 1,3-2,4_fast / 2,4-1_fast / 2,4-1_slow (shared initial condition); only 1,3-2,4_slow frame 0 differs",
            "fresh_contexts_required": 6,
            "verdict": "FRESH_WIND_AVAILABLE" if len(fresh_frames) >= 6 else "FRESH_WIND_INPUT_BLOCKED",
        },
        "fresh_mapping_proposal": {
            "note": "preregistered mapping of logical IDs to genuinely fresh configs/frames; to be locked at PHASE 2 freeze before any fresh confirmatory data is opened",
            "confirmatory": [
                {"logical_id": 10, "config": "1,3-2,4_fast", "frame": 1},
                {"logical_id": 11, "config": "1,3-2,4_slow", "frame": 1},
                {"logical_id": 12, "config": "2,4-1_slow", "frame": 1},
                {"logical_id": 13, "config": "1,3-2,4_fast", "frame": 10},
            ],
            "closed_loop": [
                {"logical_id": 14, "config": "1,3-2,4_slow", "frame": 10},
                {"logical_id": 15, "config": "2,4-1_slow", "frame": 10},
            ],
        },
        "prior_native_exercise": {
            "note": "all four configs were previously exercised by the native main_v8 PMFS forward simulator in the TADM/PMFS C0 context bank (house1_c0_context_bank_20260818, 2026-08-20). This is native forward export of a DIFFERENT method (PMFS baseline), not CTT neural M1 training/validation/diagnosis, and therefore does not consume the configs for the CTT neural M1 confirmatory test.",
            "location": "D:\\ZYC\\A-gas\\workspace\\TADM_PMFS_CODEX_FULL_20260820\\work\\context\\house1_c0_context_bank_20260818",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    OUT_JSON.write_text(text, encoding="utf-8")
    print(f"WROTE {OUT_JSON}")
    print(f"fresh_eligible_frames={len(fresh_frames)}")
    print(f"JSON_SHA256={sha256_text(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
