# Adjoint Test for GEOS Gravity modeling


## Typical Usage

### Rectangular Prism Anomaly Meshed with Tetrahedra

```bash
python gravityAdjointTest.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml --n_model 10368 --n_data 1271
```

### Rectangular Prism Anomaly Meshed with Hexahedra:

```bash
python gravityAdjointTest.py --xml ../data/rectangularPrism_C3D8/rectangularPrism_C3D8.xml --n_model 1728 --n_data 1271
```

## Typical Output

```text
=== Adjoint Test Summary ===
<Ax, y>     = 7.585858080970467e-07
<x, A^T y>  = 7.585858080970469e-07
Passed      = True
Error       = 1.2332569442944734e-16
```

