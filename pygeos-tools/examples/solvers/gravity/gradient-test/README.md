# Gradient Test for GEOS Gravity modeling


## Typical Usage

### Rectangular Prism Anomaly Meshed with Tetrahedra

```bash
python gravityGradientTest.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml --m_true ../data/rectangularPrism_C3D4/m_true.npy --m0 ../data/rectangularPrism_C3D4/m0.npy --dm ../data/rectangularPrism_C3D4/dm.npy
```

### Rectangular Prism Anomaly Meshed with Hexahedra:

```bash
python gravityGradientTest.py --xml ../data/rectangularPrism_C3D8/rectangularPrism_C3D8.xml --m_true ../data/rectangularPrism_C3D8/m_true.npy --m0 ../data/rectangularPrism_C3D8/m0.npy --dm ../data/rectangularPrism_C3D8/dm.npy
```


## Typical Output showing the expected quadratic error convergence up to machine precision
```text
         h         h2         e0         e1
5.5556e-01 3.0864e-01 6.8482e-04 1.4697e-07
3.0864e-01 9.5260e-02 3.8049e-04 4.5360e-08
1.7147e-01 2.9401e-02 2.1140e-04 1.4000e-08
9.5260e-02 9.0744e-03 1.1745e-04 4.3210e-09
5.2922e-02 2.8008e-03 6.5249e-05 1.3336e-09
2.9401e-02 8.6443e-04 3.6250e-05 4.1162e-10
1.6334e-02 2.6680e-04 2.0139e-05 1.2704e-10
9.0744e-03 8.2346e-05 1.1188e-05 3.9214e-11
5.0414e-03 2.5415e-05 6.2157e-06 1.2104e-11
2.8008e-03 7.8442e-06 3.4532e-06 3.7367e-12
1.5560e-03 2.4211e-06 1.9184e-06 1.1550e-12
8.6443e-04 7.4724e-07 1.0658e-06 3.5841e-13
4.8024e-04 2.3063e-07 5.9211e-07 1.1246e-13
2.6680e-04 7.1182e-08 3.2895e-07 3.5991e-14
1.4822e-04 2.1970e-08 1.8275e-07 1.2474e-14
8.2346e-05 6.7808e-09 1.0153e-07 6.0212e-15
4.5748e-05 2.0928e-09 5.6404e-08 3.2005e-15
2.5415e-05 6.4594e-10 3.1336e-08 2.5012e-15
1.4120e-05 1.9936e-10 1.7409e-08 2.8565e-15
7.8442e-06 6.1532e-11 9.6715e-09 2.3721e-15
4.3579e-06 1.8991e-11 5.3731e-09 2.8261e-15
2.4211e-06 5.8615e-12 2.9850e-09 2.9543e-15
1.3450e-06 1.8091e-12 1.6583e-09 2.4471e-15
7.4724e-07 5.5837e-13 9.2130e-10 2.8471e-15
4.1513e-07 1.7234e-13 5.1183e-10 2.1396e-15

=== Gradient Test Summary ===
Passed: True
Slope: [ 1.99999993  1.99999983  1.99999957  1.9999963   1.99999456  1.99997363
  1.99988094  1.99984551  1.99960117  1.99755535  1.99079356  1.97189443
  1.93835375  1.80267853  1.2392288   1.07519441  0.41943078 -0.22598208
  0.31615789 -0.29794799 -0.07551366  0.32048653 -0.25757919  0.48605047]
History saved to: grad_test.txt
```
