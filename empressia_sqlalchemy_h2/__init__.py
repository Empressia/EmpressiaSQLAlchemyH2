import sqlalchemy;
import empressia_sqlalchemy_h2;
from .CompatibilityMode import *;
from .H2DialectException import *;
from .H2Dialect import *;

sqlalchemy.dialects.registry.register("h2", empressia_sqlalchemy_h2.__name__, "H2Dialect");
