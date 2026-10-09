# PMFS P1a/P1b R2 小审核包

先读 `WIND_PARITY_VERDICT.md` 和 `CORE_PARITY_GO_NOGO.md`。本轮真实运行14个ROS/DDS/TF接口用例，整体P1a HOLD，P1b按门控未运行。

独立标准库复核：

```text
python verify_r2.py --out <新的复核结果目录>
```

脚本只读取已保存的消费者输出与运行前门限，不启动ROS或执行历史程序。它检验10个新鲜N1用例、实际GMRF已存格点/向量、三种负对照与一个延迟TF诊断，并重建CSV/时钟JSON。

真正运行过的源码和编译命令在 `evidence/real_ros/code` 与 `evidence/real_ros/build_commands.json`；原始消费者CSV、真实接收的CDR消息、风场服务查询、stdout/stderr和退出记录均保留。没有打包巨大的.o/ELF；构建出的ELF及GMRF依赖库SHA256保存在证据JSON。重新运行ROS须在独立目录准备对应构建依赖与可执行文件，不能仅凭本复核脚本声明新的端到端运行。

源码里PMFS采用共同Algorithm回调的受控子类，不是完整原样actionserver；N0记录是消息接口探针，不是完整作者示例。GMRF仅添加被动记录，核心map源验证与固定Git一致，但复用了已有共享库，不声称全量clean-build二进制等价。估计风图未给精度PASS。

`SHA256SUMS.txt`覆盖全包除自身以外的文件。`.gitattributes`保留证据字节，禁止Git自动改变行尾。原始记录与先前P0审核包均未修改。本轮没有启动或关闭已有VM，也没有产生新气体数据。
