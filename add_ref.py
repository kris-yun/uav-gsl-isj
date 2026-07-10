with open("D:/ZYC/A-gas/ASCi/sci/paper-isj-final-en/main.tex", "r", encoding="utf-8") as f:
    content = f.read()

old_ref = r'\bibitem{9} Gr\"{u}nwald, P. (2012). The safe Bayesian---learning the learning rate via the mixability gap. \emph{Proc. 23rd Intl. Conf. Algorithmic Learning Theory}, LNCS 7568, 169--183.'

new_ref = old_ref + '\n\n\\bibitem{29} Gr\"{u}nwald, P. \\& van Ommen, T. (2017). Inconsistency of Bayesian inference for misspecified linear models, and a proposal for repairing it. \\emph{Entropy}, 19(9), 466.'

content = content.replace(old_ref, new_ref)

with open("D:/ZYC/A-gas/ASCi/sci/paper-isj-final-en/main.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("Reference added")
