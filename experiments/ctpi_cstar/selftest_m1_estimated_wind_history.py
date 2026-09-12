import tempfile
from pathlib import Path
from m1_causal.estimated_wind_history import EstimatedWindHistory

def main():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'wind.txt'
        p.write_text('2 .5 .5 1 2\n2 1.5 .5 3 4\n4 .5 .5 10 20\n4 1.5 .5 30 40\n')
        h=EstimatedWindHistory.read(p,origin_xy=(0,0),cell_size=1,expected_end_s=4)
        kw={'vertical_model':'planar_extrusion_zero_vertical','initial_velocity_m_s':(0,0,0)}
        assert h.snapshot_at(1,**kw).velocity_m_s((.5,.5,0))==(0,0,0)
        assert h.snapshot_at(3.99,**kw).velocity_m_s((.5,.5,9))==(1,2,0)
        assert h.snapshot_at(4,**kw).velocity_m_s((.5,.5,9))==(10,20,0)
        assert h.snapshot_at(3,**kw).available_s==2
        try: h.snapshot_at(3,**kw).velocity_m_s((-.1,.5,0))
        except ValueError as e: assert 'UNSUPPORTED' in str(e)
        else: raise AssertionError('unsupported cell silently filled')
        try: EstimatedWindHistory.read(p,origin_xy=(.1,0),cell_size=1,expected_end_s=4)
        except ValueError: pass
        else: raise AssertionError('misaligned map accepted')
        try: EstimatedWindHistory.read(p,origin_xy=(0,0),cell_size=1,expected_end_s=240)
        except ValueError: pass
        else: raise AssertionError('partial file accepted')
        # Actual H01 t=70.8 failure: float64 row 97 vs canonical float32 row 98.
        p.write_text('2 -.90 1.97 1 2\n4 -.90 1.97 3 4\n')
        h=EstimatedWindHistory.read(p,origin_xy=(-7.55,-7.88),cell_size=.1,expected_end_s=4)
        q=(-.9181521045531363,1.9199996714520273,-.7181854996108992)
        assert h.snapshot_at(2,**kw).velocity_m_s(q)==(1,2,0)
    print('M1_ESTIMATED_WIND_HISTORY_SELFTEST_PASS')
if __name__=='__main__': main()
