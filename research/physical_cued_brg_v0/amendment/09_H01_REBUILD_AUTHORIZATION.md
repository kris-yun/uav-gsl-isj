# User-authorized House01-only model template reconstruction

The user explicitly authorized: "授权仅重建 H01 正确支持模板".

Reason: current Native fine-slice/reduction/prune support has 596 cells;
three legal cells are absent from the historical 626-cell input:
pmfs_5_18, pmfs_8_18, pmfs_7_19. An axis filter cannot create missing templates.

Preserve all historical banks. Rebuild ONLY H01 model-generated templates on
its actual Native 596-cell occupancy, retaining the frozen native simulator,
11 physical wind states, replica keys 1..8, p blur and rawu observation channel.
Keep H02 and H03 cached maps unchanged and take Native legal support views.
No new gas plume, training architecture, truth relabelling or pilot case change.
