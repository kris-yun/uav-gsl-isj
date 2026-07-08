import sys, re
sys.stdout.reconfigure(encoding='utf-8')

# Old references data (key -> full bib entry text)
old_refs = {
    "ref1": "Li, X. et al. (2026). Multi-UAV MARL for gas source localization. \\emph{arXiv:2603.11582}.",
    "ref25": "Francis, S. \\& Li, W. (2022). Gas source localization and mapping with mobile robots: A review. \\emph{Intl. J. Advanced Robotic Systems}, 19(4), 1--18.",
    "ref3": "Farrell, J.A. et al. (2002). Filament-based chemical plume tracing. \\emph{IEEE J. Oceanic Engineering}, 27(3), 526--537.",
    "ref5": "Neumann, P.P. et al. (2013). An autonomous UAV for gas source localization. \\emph{IEEE Sensors Journal}, 13(8), 3157--3166.",
    "ref23": "H{\\\"a}usler, F. et al. (2023). Bout-based gas source localization using aerial robot swarms. \\emph{IEEE Sensors Journal}, 23(24), 30456--30467.",
    "ref4": "Vergassola, M. et al. (2007). Infotaxis: Searching for a source without gradients. \\emph{Science}, 315(5813), 767--770.",
    "ge2014missing": "Ge, Q., Li, X., \\& Wen, C. (2014). Distributed Kalman filtering for sensor networked systems with randomly missing measurements. \\emph{Signal Processing}, 94, 406--417.",
    "ge2016fusion": "Ge, Q., Shao, T., Yang, Q., Shen, X., \\& Wen, C. (2016). Multisensor distributed fusion estimation with random packet losses and correlated noises. \\emph{Information Fusion}, 27, 157--167.",
    "grunwald2017safebayes": "Gr{\\\"u}nwald, P. (2012). The safe Bayesian---learning the learning rate via the mixability gap. \\emph{Proc. 23rd Intl. Conf. Algorithmic Learning Theory}, LNCS 7568, 169--183.",
    "ref22": "Shi, Y. et al. (2025). Autonomous goal detection and cessation in sequential decision making. \\emph{Proc. AAAI Conf. Artificial Intelligence}, 39(1), 20156--20164.",
    "ref10": "Ramdas, A. \\& Gr{\\\"u}nwald, P. (2023). Game-theoretic statistics and safe anytime-valid inference. \\emph{Statistical Science}, 38(4), 576--601.",
    "xu2024anytimevalid": "Xu, Z. et al. (2024). Active, Anytime-Valid Risk Controlling Prediction Sets. \\emph{NeurIPS}.",
    "lindemann2023safeplanning": "Lindemann, L. et al. (2023). Safe Planning in Dynamic Environments using Conformal Prediction. \\emph{IEEE Robotics and Automation Letters}.",
    "bissiri2016gbi": "Bissiri, P.G., Holmes, C.C., \\& Walker, S.G. (2016). General Bayesian updating and the loss-likelihood bootstrap. \\emph{Biometrika}, 103(2), 411--425.",
    "gold2007ddm": "Gold, J.I. \\& Shadlen, M.N. (2007). The neural basis of decision making. \\emph{Annual Review of Neuroscience}, 30, 535--574.",
    "ref6": "Neumann, P.P. et al. (2023). PMFS: Probabilistic mapping for gas source localization. \\emph{IEEE Trans. Robotics}, 39(2), 1234--1249.",
    "ref7": "Hutchinson, M. et al. (2019). A gas tomography approach to gas source localization. \\emph{IEEE Sensors Journal}, 19(17), 7417--7428.",
    "ref8": "Barbieri, C. \\& Cocco, S. (2021). How good is infotaxis and how to beat it. \\emph{arXiv:2104.09834}.",
    "ref20": "Kim, J. \\& Seo, J. (2024). Dual-mode information-theoretic gas source localization. \\emph{IEEE Robotics and Automation Letters}, 9(11), 9876--9883.",
    "ref19": "Ojeda, J. \\& Monroy, J. (2024). Robotic gas source localization with probabilistic mapping. \\emph{IEEE Trans. Robotics}, 40, 3215--3230.",
    "fong2021tempered": "Fong, E., Holmes, C.C., \\& Walker, S.G. (2021). Martingale posterior distributions. \\emph{J. Royal Statistical Society: Series B}, 83(5), 1014--1039.",
    "ref14": "Monroy, J. et al. (2020). GADEN: A 3D gas dispersion simulator. \\emph{IEEE Robotics \\& Automation Magazine}.",
    "ref_doob": "Doob, J.L. (1949). Application of the theory of martingales. \\emph{Colloques Internationaux du CNRS}, 13, 23--27.",
}

# Order by first appearance
ordered_keys = [
    "ref1", "ref25", "ref3", "ref5", "ref23", "ref4",
    "ge2014missing", "ge2016fusion", "grunwald2017safebayes",
    "ref22", "ref10", "xu2024anytimevalid", "lindemann2023safeplanning",
    "bissiri2016gbi", "gold2007ddm", "ref6", "ref7", "ref8",
    "ref20", "ref19", "fong2021tempered", "ref14", "ref_doob"
]

# Build new references.tex with numeric labels
lines = ["\\begin{thebibliography}{99}", ""]
for i, key in enumerate(ordered_keys, 1):
    lines.append(f"\\bibitem{{{i}}} {old_refs[key]}")
    lines.append("")
lines.append("\\end{thebibliography}")

output = "\n".join(lines)
with open(r"D:\ZYC\A-gas\ASCi\sci\paper-isj-zh-cn\sections\references.tex", 'w', encoding='utf-8') as f:
    f.write(output)
print(f"references.tex rewritten with {len(ordered_keys)} entries, numbered [1]-[{len(ordered_keys)}]")
