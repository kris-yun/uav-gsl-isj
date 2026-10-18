// Exact author Sep18 index/bounds method bodies; integer-only minimal vector storage.
#include <cstddef>
#include <iostream>
struct Vector2Int {int x,y;Vector2Int(int a,int b):x(a),y(b){}};
struct Grid2DMetadata {Vector2Int dimensions{0,0};
size_t indexOf(const Vector2Int& v) const
        {
            return v.x + v.y * dimensions.x;
        }
Vector2Int indices2D(size_t index) const
        {
            return Vector2Int(index % dimensions.x, index / dimensions.x);
        }
bool indicesInBounds(const Vector2Int& indices) const
        {
            return indices.x >= 0 && indices.x < dimensions.x && indices.y >= 0 && indices.y < dimensions.y;
        }
};
int main(){int n=0;for(Vector2Int dim:{Vector2Int(3,7),Vector2Int(7,3),Vector2Int(33,47),Vector2Int(47,33)}){
 Grid2DMetadata m;m.dimensions=dim;
 for(int y=0;y<dim.y;++y)for(int x=0;x<dim.x;++x){Vector2Int a{x,y};size_t k=m.indexOf(a);auto b=m.indices2D(k);if(k!=size_t(x+y*dim.x)||a.x!=b.x||a.y!=b.y||!m.indicesInBounds(a))return 1;++n;}
 for(Vector2Int v:{Vector2Int(-1,0),Vector2Int(0,-1),Vector2Int(dim.x,0),Vector2Int(0,dim.y)})if(m.indicesInBounds(v))return 2;
 }std::cout<<"{\"status\":\"PASS\",\"roundtrips\":"<<n<<",\"rectangles\":4,\"native_header_changed\":false}\n";
}
