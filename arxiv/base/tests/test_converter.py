
from werkzeug.routing import Map, Rule

from arxiv.base.converter import ArXivConverter

url_map = Map([
    Rule('/', endpoint='blog/index'),
    Rule('/<int:year>/', endpoint='blog/archive'),
])

def test_converter():
    converter = ArXivConverter(url_map)

    # Throws
    # print( converter.to_python( "this is a test" ) )
    # Throws (why?)
    # print( converter.to_python( "math/0034566" ) )

    id = "2012.01234v3"
    assert id == converter.to_python(id)
    assert id == converter.to_url(id)


