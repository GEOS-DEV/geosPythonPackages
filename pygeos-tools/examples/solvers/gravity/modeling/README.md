# Gravity Modeling


## Typical Usage

### Rectangular Prism Anomaly Meshed with Tetrahedra

```bash
python gravityModeling.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml --m_true ../data/rectangularPrism_C3D4/m_true.npy
```
or equivalently:
```bash
python gravityModelingLinearOp.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml --m_true ../data/rectangularPrism_C3D4/m_true.npy
```

### Rectangular Prism Anomaly Meshed with Hexahedra:

```bash
python gravityModeling.py --xml ../data/rectangularPrism_C3D8/rectangularPrism_C3D8.xml --m_true ../data/rectangularPrism_C3D8/m_true.npy
```
or equivalently:
```bash
python gravityModelingLinearOp.py --xml ../data/rectangularPrism_C3D8/rectangularPrism_C3D8.xml --m_true ../data/rectangularPrism_C3D8/m_true.npy
```

