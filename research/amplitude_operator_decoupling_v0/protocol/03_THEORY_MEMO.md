# Theory memo: resolution vs robustness

This memo is a candidate theory direction, not yet a paper claim.

Let `m_theta(x)` be a source-location-dependent amplitude field and `G_sigma`
a normalized Gaussian blur.

For a local source-location parameter theta and additive iid Gaussian
measurement noise, Fisher information is proportional to

`|| d m_theta / d theta ||_2^2`.

Since differentiation commutes with convolution,

`d(G_sigma * m_theta)/dtheta = G_sigma * (d m_theta/dtheta)`.

A normalized Gaussian convolution is an L2 contraction, hence in the ideal
linear/free-space setting

`||G_sigma * d m_theta/dtheta||_2 <= ||d m_theta/dtheta||_2`.

Therefore extra smoothing cannot increase the local amplitude-channel Fisher
information for source position under that observation model.

This gives a principled explanation for the observed trade-off:

- smoothing can reduce model mismatch / numerical noise in the binary
  occurrence channel;
- the same smoothing can suppress high-spatial-frequency differences needed to
  discriminate sources separated by less than the blur scale.

The intended method is NOT “turn blur off everywhere”.

It is:

**use channel-specific observation operators**
- robust/native operator for occurrence;
- physical sampling operator for amplitude;
- do not reuse numerical regularization as a sensor observation kernel.

This connects to modern computational imaging, where physical image formation
(PSF / observation operator) is modeled separately from restoration or
regularization.
