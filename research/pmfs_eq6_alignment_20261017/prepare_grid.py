from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
p=R/'author_release/gsl_server/src/gsl_server/algorithms/Common/Grid2D.hpp'
text=p.read_text()
def extract(signature):
    start=text.index(signature);a=text.index('{',start);depth=0
    for b in range(a,len(text)):
        depth+=(text[b]=='{')-(text[b]=='}')
        if depth==0:return text[start:b+1]
    raise ValueError(signature)
parts=[extract(s)for s in ['size_t indexOf(', 'Vector2Int indices2D(', 'bool indicesInBounds(']]
code='''// Exact author Sep18 index/bounds method bodies; integer-only minimal vector storage.
#include <cstddef>
#include <iostream>
struct Vector2Int {int x,y;Vector2Int(int a,int b):x(a),y(b){}};
struct Grid2DMetadata {Vector2Int dimensions{0,0};
'''+ '\n'.join(parts)+'''
};
int main(){int n=0;for(Vector2Int dim:{Vector2Int(3,7),Vector2Int(7,3),Vector2Int(33,47),Vector2Int(47,33)}){
 Grid2DMetadata m;m.dimensions=dim;
 for(int y=0;y<dim.y;++y)for(int x=0;x<dim.x;++x){Vector2Int a{x,y};size_t k=m.indexOf(a);auto b=m.indices2D(k);if(k!=size_t(x+y*dim.x)||a.x!=b.x||a.y!=b.y||!m.indicesInBounds(a))return 1;++n;}
 for(Vector2Int v:{Vector2Int(-1,0),Vector2Int(0,-1),Vector2Int(dim.x,0),Vector2Int(0,dim.y)})if(m.indicesInBounds(v))return 2;
 }std::cout<<"{\\"status\\":\\"PASS\\",\\"roundtrips\\":"<<n<<",\\"rectangles\\":4,\\"native_header_changed\\":false}\\n";
}
'''
out=R/'cpp/grid_probe.cpp';assert not out.exists();out.write_text(code,encoding='utf-8',newline='\n')
plan=dict(scope='Integer indexing/inverse/bounds only. Not a complete September ROS grid or navigation qualification.',source=str(p),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_bodies_unmodified=True,dimensions=[[3,7],[7,3],[33,47],[47,33]],expected_roundtrips=3144,source_changes=0,new_worlds=0,new_ROS=0)
(R/'GRID_COMPONENT_PRECOMMIT.json').write_text(json.dumps(plan,indent=2))
print(json.dumps(plan))
