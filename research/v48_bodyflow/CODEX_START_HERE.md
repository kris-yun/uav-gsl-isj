# V48：恢复V47、定位V46断点，不以假阴性或假阳性代替验证

先读 `CODEX_EXECUTION_CONTRACT.md`。本目录基于固定V46提交 `9326fb9e91bfbabcafb4320529382dd9a0b0c885`，不覆盖旧证据。

已查明：三场M1正读数2725/6254/9003在冻结真源三模板上的均值全部为0；不同控制轨迹可落到同一错误后验；V46短名单未保护三路代表；原目录282个仅停驻状态全部存在半速合法运动。不能据此宣称修复后M1必胜，也不能归因于数据一概太平滑。

## 代码

仓库包含完整可应用的方法差分 `core_v46_to_v48.patch` 和原生适配器。运行：

```bash
python3 research/v48_bodyflow/bootstrap.py --output /absolute/new/path/v48_runtime
cd /absolute/new/path/v48_runtime
python3 -m pip install -r requirements.txt
python3 tests/test_chain.py
```

bootstrap校验原core、补丁及最终core哈希，复制原V46完整包后应用V47分支代表/强普通对照和V48共享目录细化，不修改原目录。使用`v47_flowolf`命名空间保持与交付ZIP兼容。默认速度层仍为`(1.0,)`，新层必须显式设为`(1,.5,.25,.125,.0625)`并给予全部对照。

完整交付的 `V48_Code_and_Contract.zip` 还包含13个数学/软件入口、9个冻结原生接入检查及全部只读审计脚本；本仓库差分目录不冒称含有全部本地证书和原始数据。使用完整ZIP时执行 `python3 verify_all.py`，再按合同复核上传的两个原始tar卷。

`native_adapter_v48.py`保留原V46 NativePosterior与端点EIG，禁止用Green环境替代原生数据。原B0仍未物理合格，适配成功不等于前向修复。当前不新增住宅或种子，不填新定位成绩。
