"""Small asymmetric-map checks independent of House geometry."""
from pathlib import Path
from tempfile import TemporaryDirectory
from m1_causal.occupancy3d import Occupancy3D


def main():
    raw='#env_min(m) -1 -2 -3\n#env_max(m) 1 1 -1\n#num_cells 2 3 2\n#cell_size(m) 1\n0 1 2\n2 0 1\n;\n1 2 0\n0 1 2\n;\n'
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/'map.csv'
        path.write_text(raw)
        m=Occupancy3D.read(path)
        assert m.cells.shape==(2,3,2)
        assert m.state((-.5,-1.5,-2.5))==0
        assert m.state((.5,-1.5,-2.5))==2
        assert m.state((-.5,.5,-1.5))==0
        assert m.state((1.,-1.5,-2.5))==3
        assert not m.cells.flags.writeable
        for malformed in (raw.replace('0 1 2','0 1',1),raw.replace('0 1 2','0 1 255',1),raw.rsplit(';',2)[0]):
            path.write_text(malformed)
            try:
                Occupancy3D.read(path)
            except ValueError:
                pass
            else:
                raise AssertionError('malformed occupancy accepted')
    print('M1_OCCUPANCY3D_SELFTEST=PASS')


if __name__=='__main__':
    main()
