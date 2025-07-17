# Gravity Modeling


## Typical Usage

### Rectangular Prism Anomaly Meshed with Tetrahedra

To use the density model defined in the XML file:
```bash
python gravityModeling.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml  --save_gz gz_C3D4.npy
```

Alternatively, override the XML-defined model by providing a custom model as a NumPy array:
```bash
python gravityModeling.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml --model ../data/rectangularPrism_C3D4/m_true.npy --save_gz gz_C3D4.npy
```
or equivalently:
```bash
python gravityModelingLinearOp.py --xml ../data/rectangularPrism_C3D4/rectangularPrism_C3D4.xml --model ../data/rectangularPrism_C3D4/m_true.npy --save_gz gz_C3D4.npy
```

### Rectangular Prism Anomaly Meshed with Hexahedra:

```bash
python gravityModeling.py --xml ../data/rectangularPrism_C3D8/rectangularPrism_C3D8.xml --model ../data/rectangularPrism_C3D8/m_true.npy --save_gz gz_C3D8.npy
```
or equivalently:
```bash
python gravityModelingLinearOp.py --xml ../data/rectangularPrism_C3D8/rectangularPrism_C3D8.xml --model ../data/rectangularPrism_C3D8/m_true.npy --save_gz gz_C3D8.npy
```

